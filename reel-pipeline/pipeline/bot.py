"""Den Den Mushi: the Telegram bot. Share a reel, pick a crew member, and Grand Log files it.

Long-polling, so it runs behind NAT with no public URL. A shared link gets three buttons
(Baratie, Log Pose, Going Merry). The choice goes to a SQLite queue, a background worker runs
the pipeline in a thread, and the bot replies with the result.

Run: python -m pipeline.bot   (set TELEGRAM_BOT_TOKEN in .env)
"""
from __future__ import annotations

import asyncio
import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from . import config, queue, security, store
from .process import process_one
from .routing import BUCKETS, NAMES

_EMOJI = {"recipe": "\U0001f373", "place": "\U0001f5fe", "home": "\U0001f3e0"}
_BUCKETS = [(bucket, f"{_EMOJI.get(bucket, '')} {NAMES[bucket]}".strip()) for bucket in BUCKETS]


async def _authorized(update: Update) -> bool:
    """Gate every interaction to the owner. Unknown chats are told their id, then ignored."""
    chat = update.effective_chat
    if chat is None:
        return False
    if security.is_allowed_chat(chat.id):
        return True
    message = update.effective_message
    if message:
        if not config.ALLOWED_CHAT_IDS and not config.ALLOW_ALL_CHATS:
            await message.reply_text(
                f"Locked. Your chat id is {chat.id}. Add ALLOWED_CHAT_IDS={chat.id} to your .env "
                "and restart to start using Grand Log.")
        else:
            await message.reply_text("Not authorized.")
    return False


async def on_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A message with a link: remember it for this chat and offer the crew buttons."""
    if not await _authorized(update):
        return
    url = security.first_allowed_url(update.message.text or "")
    if not url:
        await update.message.reply_text(
            "Send a reel link from a supported site (Instagram, TikTok, YouTube, and similar).")
        return
    context.chat_data["url"] = url
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data=bucket)] for bucket, label in _BUCKETS]
    )
    await update.message.reply_text("Where does this treasure go?", reply_markup=keyboard)


async def on_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A button tap: enqueue the job for the chosen crew member."""
    if not await _authorized(update):
        return
    query = update.callback_query
    await query.answer()
    url = context.chat_data.get("url")
    if not url:
        await query.edit_message_text("Share the reel again, please.")
        return
    bucket = query.data
    if bucket not in BUCKETS:
        await query.edit_message_text("Unknown crew member.")
        return
    queue.enqueue(url, bucket, query.message.chat_id)
    await query.edit_message_text(f"Queued for {NAMES[bucket]}. I will report back when it is filed.")


def _result_lines(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        line = f"• {row.get('title') or 'untitled'} ({NAMES.get(row.get('bucket'), row.get('bucket'))})"
        if row.get("link"):
            line += f"\n  {row['link']}"
        lines.append(line)
    return "\n".join(lines)


async def _send_card(app: Application, chat_id: int, bucket: str, card: dict) -> None:
    """Send the rich capture card: thumbnail, title, one-line summary, and an Open button."""
    caption = f"{NAMES.get(bucket, 'Grand Log')} filed\n{card.get('title', '')}\n{card.get('summary', '')}".strip()
    markup = None
    if card.get("link"):
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("Open", url=card["link"])]])
    thumb = card.get("thumb")
    if thumb and os.path.exists(thumb):
        with open(thumb, "rb") as photo:
            await app.bot.send_photo(chat_id, photo=photo, caption=caption, reply_markup=markup)
    else:
        await app.bot.send_message(chat_id, caption, reply_markup=markup)


async def on_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/search <term>: find anything you have saved."""
    if not await _authorized(update):
        return
    term = " ".join(context.args).strip()
    if not term:
        await update.message.reply_text("Usage: /search <term>")
        return
    rows = store.search(term)
    await update.message.reply_text(_result_lines(rows) if rows else f"No matches for '{term}'.")


async def on_digest(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/digest: a few saved items to revisit, the resurfacing nudge."""
    if not await _authorized(update):
        return
    rows = store.sample(5)
    if not rows:
        await update.message.reply_text("Nothing saved yet. Share a reel to get started.")
        return
    await update.message.reply_text("A few to revisit:\n" + _result_lines(rows))


async def on_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/dashboard: open the tile dashboard, as a Mini App if WEBAPP_URL is an https link."""
    if not await _authorized(update):
        return
    url = config.WEBAPP_URL
    if not url:
        await update.message.reply_text(
            "Run the dashboard with `python -m pipeline.web`, then set WEBAPP_URL in .env to its URL.")
        return
    if url.startswith("https://"):
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("Open dashboard", web_app=WebAppInfo(url))]])
        await update.message.reply_text("Your Grand Log", reply_markup=markup)
    else:
        await update.message.reply_text(f"Dashboard: {url}")


async def _worker(app: Application) -> None:
    """Claim jobs one at a time, run the pipeline in a thread, and report back. Never dies."""
    while True:
        job = queue.claim_next()
        if job is None:
            await asyncio.sleep(5)
            continue
        if job["bucket"] not in BUCKETS:
            queue.mark_failed(job["id"], "unknown bucket")
            continue
        try:
            record = await asyncio.to_thread(process_one, job["url"], job["bucket"], False)
            card = record.get("_card", {})
            queue.mark_done(job["id"], card.get("title", "it"))
            if job["chat_id"]:  # backfill jobs carry chat_id 0, no one to reply to
                await _send_card(app, job["chat_id"], job["bucket"], card)
        except Exception as exc:  # keep the worker alive no matter what one job does
            queue.mark_failed(job["id"], str(exc))
            if job["chat_id"]:
                try:
                    await app.bot.send_message(job["chat_id"], f"That one failed: {exc}")
                except Exception:
                    pass


async def _post_init(app: Application) -> None:
    queue.init_db()
    store.init_db()
    app.create_task(_worker(app))


def main() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env (get one from @BotFather).")
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(_post_init).build()
    app.add_handler(CommandHandler("search", on_search))
    app.add_handler(CommandHandler("digest", on_digest))
    app.add_handler(CommandHandler("dashboard", on_dashboard))
    app.add_handler(CallbackQueryHandler(on_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_link))
    app.run_polling()


if __name__ == "__main__":
    main()

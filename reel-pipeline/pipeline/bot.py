"""Den Den Mushi: the Telegram bot. Share a reel, pick a crew member, and Grand Log files it.

Long-polling, so it runs behind NAT with no public URL. A shared link gets three buttons
(Baratie, Log Pose, Going Merry). The choice goes to a SQLite queue, a background worker runs
the pipeline in a thread, and the bot replies with the result.

Run: python -m pipeline.bot   (set TELEGRAM_BOT_TOKEN in .env)
"""
from __future__ import annotations

import asyncio
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from . import config, queue
from .process import NAMES, process_one

_URL = re.compile(r"https?://\S+")
_BUCKETS = [("recipe", "\U0001f373 Baratie"), ("japan", "\U0001f5fe Log Pose"), ("home", "\U0001f3e0 Going Merry")]


async def on_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A message with a link: remember it for this chat and offer the crew buttons."""
    match = _URL.search(update.message.text or "")
    if not match:
        return
    context.chat_data["url"] = match.group(0)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton(label, callback_data=bucket)] for bucket, label in _BUCKETS]
    )
    await update.message.reply_text("Where does this treasure go?", reply_markup=keyboard)


async def on_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """A button tap: enqueue the job for the chosen crew member."""
    query = update.callback_query
    await query.answer()
    url = context.chat_data.get("url")
    if not url:
        await query.edit_message_text("Share the reel again, please.")
        return
    bucket = query.data
    if bucket not in ("recipe", "japan"):
        await query.edit_message_text(f"{NAMES.get(bucket, bucket)} is not aboard yet. Baratie and Log Pose are live.")
        return
    queue.enqueue(url, bucket, query.message.chat_id)
    await query.edit_message_text(f"Queued for {NAMES[bucket]}. I will report back when it is filed.")


async def _worker(app: Application) -> None:
    """Claim jobs one at a time, run the pipeline in a thread, and report back. Never dies."""
    while True:
        job = queue.claim_next()
        if job is None:
            await asyncio.sleep(5)
            continue
        if job["bucket"] not in ("recipe", "japan"):  # Going Merry is not aboard yet
            queue.mark_failed(job["id"], "bucket not aboard yet")
            continue
        try:
            recipe = await asyncio.to_thread(process_one, job["url"], job["bucket"], False)
            title = recipe.get("title", "your recipe")
            queue.mark_done(job["id"], title)
            if job["chat_id"]:  # backfill jobs carry chat_id 0, no one to reply to
                await app.bot.send_message(job["chat_id"], f"Baratie filed it: {title}")
        except Exception as exc:  # keep the worker alive no matter what one job does
            queue.mark_failed(job["id"], str(exc))
            if job["chat_id"]:
                try:
                    await app.bot.send_message(job["chat_id"], f"That one failed: {exc}")
                except Exception:
                    pass


async def _post_init(app: Application) -> None:
    queue.init_db()
    app.create_task(_worker(app))


def main() -> None:
    if not config.TELEGRAM_BOT_TOKEN:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in .env (get one from @BotFather).")
    app = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(_post_init).build()
    app.add_handler(CallbackQueryHandler(on_choice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_link))
    app.run_polling()


if __name__ == "__main__":
    main()

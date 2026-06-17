"""Unit tests for the bot's access gate: every handler funnels through _authorized, which
locks Den Den Mushi to the owner. Duck-typed Update stand-ins, no Telegram server, no network."""
import asyncio

from pipeline import bot, config


class _Msg:
    def __init__(self):
        self.replies = []

    async def reply_text(self, text, **kw):
        self.replies.append(text)


class _Chat:
    def __init__(self, cid):
        self.id = cid


class _Update:
    def __init__(self, cid, text=""):
        self.effective_chat = _Chat(cid) if cid is not None else None
        self.effective_message = _Msg()
        self.message = self.effective_message
        self.message.text = text


def _lock(monkeypatch, allowed):
    monkeypatch.setattr(config, "ALLOW_ALL_CHATS", False)
    monkeypatch.setattr(config, "ALLOWED_CHAT_IDS", allowed)


def test_authorized_allows_owner(monkeypatch):
    _lock(monkeypatch, {42})
    assert asyncio.run(bot._authorized(_Update(42))) is True


def test_authorized_rejects_stranger(monkeypatch):
    _lock(monkeypatch, {42})
    update = _Update(7)
    assert asyncio.run(bot._authorized(update)) is False
    assert update.effective_message.replies == ["Not authorized."]


def test_authorized_fails_closed_without_chat(monkeypatch):
    _lock(monkeypatch, {42})
    assert asyncio.run(bot._authorized(_Update(None))) is False


def test_unconfigured_bot_tells_chat_its_id(monkeypatch):
    _lock(monkeypatch, set())  # no allow-list yet: self-onboarding path
    update = _Update(7)
    assert asyncio.run(bot._authorized(update)) is False
    assert any("7" in r and "ALLOWED_CHAT_IDS" in r for r in update.effective_message.replies)


def test_on_link_bails_for_stranger_before_url_work(monkeypatch):
    _lock(monkeypatch, {42})

    def boom(text):
        raise AssertionError("url extraction ran past the access gate")

    monkeypatch.setattr(bot.security, "first_allowed_url", boom)
    update = _Update(7, text="https://instagram.com/reel/abc/")
    ctx = type("Ctx", (), {"chat_data": {}})()
    asyncio.run(bot.on_link(update, ctx))
    assert "url" not in ctx.chat_data

"""Saved-items store: one row per filed reel, for search and resurfacing.

Separate from the job queue. /search and /digest read this, and the future tile
dashboard will render the same rows. Capture goes into a destination per kind
(Mealie, a map, a vault); this is the unified index over all of them.
"""
from __future__ import annotations

import sqlite3

from . import config

_DB = config.WORKDIR / "items.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                bucket     TEXT NOT NULL,
                title      TEXT,
                summary    TEXT,
                link       TEXT,
                thumb      TEXT,
                text       TEXT,
                source_url TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )"""
        )


def save(bucket: str, title: str = "", summary: str = "", link: str = "",
         thumb: str = "", text: str = "", source_url: str = "") -> int:
    init_db()
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO items (bucket, title, summary, link, thumb, text, source_url) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (bucket, title, summary, link, thumb, text, source_url),
        )
        return int(cur.lastrowid)


def search(term: str, limit: int = 10) -> list[dict]:
    init_db()
    like = f"%{term}%"
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE title LIKE ? OR text LIKE ? ORDER BY id DESC LIMIT ?",
            (like, like, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def recent(limit: int = 5) -> list[dict]:
    init_db()
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM items ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]


def get(item_id: int) -> dict | None:
    init_db()
    with _conn() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    return dict(row) if row else None


def exists(source_url: str) -> bool:
    """True if this source URL is already saved, so a backfill can resume and skip duplicates."""
    if not source_url:
        return False
    init_db()
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM items WHERE source_url = ? LIMIT 1", (source_url,)).fetchone()
    return row is not None


def sample(limit: int = 5) -> list[dict]:
    """A few items to resurface. Random so the pile does not go stale and the digest stays small."""
    init_db()
    with _conn() as conn:
        rows = conn.execute("SELECT * FROM items ORDER BY RANDOM() LIMIT ?", (limit,)).fetchall()
    return [dict(row) for row in rows]

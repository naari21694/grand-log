"""SQLite job queue for Den Den Mushi. Resumable: jobs survive a restart.

One row per shared reel: url, bucket, chat_id, status (pending, running, done, failed).
A single worker claims jobs, which keeps the claim simple and race-free.
"""
from __future__ import annotations

import sqlite3

from . import config

_DB = config.WORKDIR / "queue.db"


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the table and reset any job left 'running' by a crash."""
    with _conn() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS jobs (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                url        TEXT    NOT NULL,
                bucket     TEXT    NOT NULL,
                chat_id    INTEGER NOT NULL,
                status     TEXT    NOT NULL DEFAULT 'pending',
                result     TEXT,
                error      TEXT,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )"""
        )
        conn.execute("UPDATE jobs SET status='pending' WHERE status='running'")


def enqueue(url: str, bucket: str, chat_id: int) -> int:
    with _conn() as conn:
        cur = conn.execute(
            "INSERT INTO jobs (url, bucket, chat_id) VALUES (?, ?, ?)", (url, bucket, chat_id)
        )
        return int(cur.lastrowid)


def claim_next() -> dict | None:
    """Return the oldest pending job and mark it running, or None if the queue is empty."""
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM jobs WHERE status='pending' ORDER BY id LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        conn.execute("UPDATE jobs SET status='running' WHERE id=?", (row["id"],))
        return dict(row)


def mark_done(job_id: int, result: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE jobs SET status='done', result=? WHERE id=?", (result, job_id))


def mark_failed(job_id: int, error: str) -> None:
    with _conn() as conn:
        conn.execute("UPDATE jobs SET status='failed', error=? WHERE id=?", (error[:1000], job_id))

import sqlite3

from pipeline import queue


def test_enqueue_then_claim_returns_oldest(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, "_DB", tmp_path / "q.db")
    queue.init_db()
    first = queue.enqueue("urlA", "recipe", 1)
    second = queue.enqueue("urlB", "recipe", 1)
    job = queue.claim_next()
    assert job["id"] == first and job["url"] == "urlA"
    assert queue.claim_next()["id"] == second


def test_claim_marks_running_so_empty_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, "_DB", tmp_path / "q.db")
    queue.init_db()
    queue.enqueue("u", "recipe", 1)
    queue.claim_next()
    assert queue.claim_next() is None


def test_init_resets_orphaned_running_jobs(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, "_DB", tmp_path / "q.db")
    queue.init_db()
    queue.enqueue("u", "recipe", 1)
    queue.claim_next()          # now running
    queue.init_db()             # simulate a restart
    assert queue.claim_next() is not None


def test_mark_done_leaves_nothing_pending(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, "_DB", tmp_path / "q.db")
    queue.init_db()
    job_id = queue.enqueue("u", "recipe", 1)
    queue.claim_next()
    queue.mark_done(job_id, "Title")
    assert queue.claim_next() is None


def test_mark_retry_holds_job_until_backoff_elapses(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, "_DB", tmp_path / "q.db")
    queue.init_db()
    job_id = queue.enqueue("u", "recipe", 1)
    queue.claim_next()
    queue.mark_retry(job_id, "blip", attempts=1, delay_seconds=3600)
    assert queue.claim_next() is None  # requeued but not due yet


def test_mark_retry_due_now_is_claimable_with_attempts(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, "_DB", tmp_path / "q.db")
    queue.init_db()
    job_id = queue.enqueue("u", "recipe", 1)
    queue.claim_next()
    queue.mark_retry(job_id, "blip", attempts=1, delay_seconds=0)
    job = queue.claim_next()
    assert job is not None and job["attempts"] == 1


def test_init_db_migrates_a_pre_retry_database(tmp_path, monkeypatch):
    db = tmp_path / "q.db"
    monkeypatch.setattr(queue, "_DB", db)
    with sqlite3.connect(db) as conn:  # the old schema, before attempts/next_at existed
        conn.execute(
            "CREATE TABLE jobs (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT NOT NULL, "
            "bucket TEXT NOT NULL, chat_id INTEGER NOT NULL, status TEXT NOT NULL DEFAULT 'pending', "
            "result TEXT, error TEXT, created_at TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        conn.execute("INSERT INTO jobs (url, bucket, chat_id) VALUES ('u', 'recipe', 1)")
    queue.init_db()  # must add the new columns without error
    job = queue.claim_next()
    assert job is not None and job["attempts"] == 0

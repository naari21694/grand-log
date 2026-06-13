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

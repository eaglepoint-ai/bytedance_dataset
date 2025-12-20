import threading
import time

import notify_service


def test_uses_concurrency_and_respects_global_limit(monkeypatch):
    """
    FAIL_TO_PASS-style test.

    - Before refactor (synchronous): max_concurrent == 1 -> FAIL
    - After refactor (bounded concurrency): 2 <= max_concurrent <= 50 -> PASS
    """
    lock = threading.Lock()
    active = 0
    max_active = 0

    def fake_send(user_id, payload):
        nonlocal active, max_active
        with lock:
            active += 1
            if active > max_active:
                max_active = active
        time.sleep(0.01)
        with lock:
            active -= 1
        return f"sent:{user_id}"

    monkeypatch.setattr(notify_service, "send_notification", fake_send)

    user_ids = list(range(200))
    _ = notify_service.notify_users(user_ids, "p")

    assert max_active >= 2, f"expected concurrent sends, got max_active={max_active}"
    assert max_active <= 50, f"expected global limit of 50, got max_active={max_active}"

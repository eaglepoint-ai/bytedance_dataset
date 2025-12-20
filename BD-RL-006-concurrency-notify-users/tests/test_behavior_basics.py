import notify_service
import pytest


def test_order_and_error_alignment(monkeypatch):
    """results[i] must correspond to user_ids[i], including errors."""
    calls = []

    def fake_send(user_id, payload):
        calls.append(user_id)
        if user_id % 3 == 0:
            raise RuntimeError(f"boom:{user_id}")
        return f"sent:{user_id}:{payload}"

    monkeypatch.setattr(notify_service, "send_notification", fake_send)

    user_ids = list(range(10))
    payload = "X"
    results = notify_service.notify_users(user_ids, payload)

    assert len(results) == len(user_ids)
    for i, uid in enumerate(user_ids):
        if uid % 3 == 0:
            assert results[i] == f"boom:{uid}"
        else:
            assert results[i] == f"sent:{uid}:{payload}"


def test_keyboard_interrupt_propagates(monkeypatch):
    """Fatal errors like KeyboardInterrupt must not be swallowed."""

    def fake_send(user_id, payload):
        if user_id == 2:
            raise KeyboardInterrupt()
        return f"sent:{user_id}"

    monkeypatch.setattr(notify_service, "send_notification", fake_send)

    user_ids = [0, 1, 2, 3]

    with pytest.raises(KeyboardInterrupt):
        notify_service.notify_users(user_ids, "payload")


def test_notify_users_is_callable_and_returns_list():
    """Basic smoke test: returns a list of same length as input."""
    user_ids = [1, 2, 3, 4]
    out = notify_service.notify_users(user_ids, "p")
    assert isinstance(out, list)
    assert len(out) == len(user_ids)

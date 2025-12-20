import time
import random

# DO NOT MODIFY THIS FUNCTION
def send_notification(user_id, payload):
    """Simulates a slow I/O-bound notification send."""
    time.sleep(0.02)
    if random.random() < 0.05:
        raise RuntimeError("send failed")
    return f"sent:{user_id}"


# TASK: Optimize this function
def notify_users(user_ids, payload):
    results = []
    for user_id in user_ids:
        try:
            # Simulate user lookup (expensive)
            time.sleep(0.01)
            result = send_notification(user_id, payload)
            results.append(result)
        except Exception as e:  # noqa: BLE001
            results.append(str(e))
    return results

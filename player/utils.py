import time

from shared.utils import FlagBoolean


def wait_until(target_time: float) -> None:
    """Pause execution until the specified target time (in seconds since the epoch)."""
    while time.time() < target_time:
        time.sleep(
            max(min((target_time - time.time()) / 2, 0.01), 0.001)
        )  # Sleep briefly to avoid busy waiting


def wait_until_or_cancel(target_time: float, cancel_flag: FlagBoolean) -> bool:
    """Pause execution until the specified target time (in seconds since the epoch) or until canceled.
    Returns True if the wait completed, False if it was canceled.
    """
    while time.time() < target_time:
        if cancel_flag.get():
            return False
        time.sleep(
            max(min((target_time - time.time()) / 2, 0.01), 0.001)
        )  # Sleep briefly to avoid busy waiting
    return True

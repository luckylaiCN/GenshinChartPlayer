import time


class FlagBoolean:
    condition: bool

    def __init__(self, condition: bool = False) -> None:
        self.condition = condition

    def modify(self, condition: bool) -> None:
        self.condition = condition

    def get(self) -> bool:
        return self.condition


def wait_until(target_time: float) -> None:
    """Pause execution until the specified target time (in seconds since the epoch)."""
    while time.time() < target_time:
        time.sleep(
            min((target_time - time.time()) / 2, 0.01)
        )  # Sleep briefly to avoid busy waiting


def wait_until_or_cancel(target_time: float, cancel_flag: FlagBoolean) -> bool:
    """Pause execution until the specified target time (in seconds since the epoch) or until canceled.
    Returns True if the wait completed, False if it was canceled.
    """
    while time.time() < target_time:
        if cancel_flag.condition:
            return False
        time.sleep(
            min((target_time - time.time()) / 2, 0.01)
        )  # Sleep briefly to avoid busy waiting
    return True

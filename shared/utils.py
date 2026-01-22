import os
import sys
import ctypes

from enum import Enum

PROJECT_ROOT: str

if getattr(sys, "frozen", False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    PROJECT_ROOT = sys._MEIPASS  # type: ignore
    PROJECT_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))
else:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))  # type: ignore
    PROJECT_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))


def rpath(*paths: str) -> str:
    """Get the absolute path relative to the project root."""
    return os.path.join(PROJECT_ROOT, *paths)


AUDIO_DIR = rpath("audio")


class OperatingSystem(Enum):
    WINDOWS = "Windows"
    LINUX = "Linux"
    MACOS = "Darwin"


def get_operating_system() -> OperatingSystem:
    platform = sys.platform
    if platform.startswith("win"):
        return OperatingSystem.WINDOWS
    elif platform.startswith("linux"):
        return OperatingSystem.LINUX
    elif platform.startswith("darwin"):
        return OperatingSystem.MACOS
    else:
        raise RuntimeError(f"Unsupported operating system: {platform}")


CURRENT_OS = get_operating_system()


def check_admin_privileges() -> bool:
    """Check if the current process has administrative privileges."""
    try:
        if CURRENT_OS == OperatingSystem.WINDOWS:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0  # type: ignore
        else:
            return os.geteuid() == 0  # type: ignore
    except Exception:
        return False


IS_ADMIN = check_admin_privileges()


def ask_for_admin_privileges() -> None:
    """Relaunch the current script with administrative privileges.
    Note: This will terminate the current process.
    """
    if CURRENT_OS == OperatingSystem.WINDOWS:
        import ctypes

        params = " ".join([f'"{arg}"' for arg in sys.argv])
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, params, None, 1
        )
        sys.exit(0)
    else:
        pass


def should_request_admin_privileges() -> bool:
    """Determine whether the application should request admin privileges."""
    if CURRENT_OS == OperatingSystem.WINDOWS:
        return not IS_ADMIN
    else:
        return False


class OperationLockState(Enum):
    FREE = "Free"
    PLAYING = "Playing"
    PRACTICING = "Practicing"


class OperationLock:
    state: OperationLockState = OperationLockState.FREE

    def __init__(self) -> None:
        pass

    def is_free(self) -> bool:
        return self.state == OperationLockState.FREE

    def set_state(self, new_state: OperationLockState) -> None:
        self.state = new_state

    def release(self) -> None:
        self.state = OperationLockState.FREE

    def locked(self) -> bool:
        return self.state != OperationLockState.FREE


global_operation_lock = OperationLock()

WARNING_CHARACTER = "⚠️"
ERROR_CHARACTER = "❌"

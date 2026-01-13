import keyboard

from player.pattern import NoteContainer
from player.utils import FlagBoolean, wait_until_or_cancel


def handler(
    note_container: NoteContainer, cancel_flag: FlagBoolean, begin_time: float
) -> None:
    status = wait_until_or_cancel(note_container.play_time + begin_time, cancel_flag)
    if status:
        kb = note_container.note.keyboard
        if kb is not None:
            keyboard.press_and_release(kb)


def available() -> bool:
    try:
        keyboard.write("")  # Test if keyboard module is functional
        return True
    except Exception:
        return False


def name() -> str:
    return "键盘输入"

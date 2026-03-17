from player.pattern import NoteContainer
from player.utils import FlagBoolean


def handler(
    note_container: NoteContainer, cancel_flag: FlagBoolean, begin_time: float
) -> None:
    pass


def available() -> bool:
    return True


def name() -> str:
    return "Do Nothing"

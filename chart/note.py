from abc import ABC, abstractmethod

from chart.constants import ChartNotation, CONTINUE_TOKEN
from chart.utils import token_to_keyboard, token_to_index


class BasicNote(ABC):
    """An abstract base class for chart notes."""

    @abstractmethod
    def __eq__(self, value: object) -> bool:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __gt__(self, value: object) -> bool:
        pass

    @abstractmethod
    def copy(self) -> "BasicNote":
        pass

    @abstractmethod
    def __hash__(self) -> int:
        pass

    @abstractmethod
    def standardized_str(self) -> str:
        pass


class ContinuousNote(BasicNote):
    """A class representing a continue chart note."""

    def __eq__(self, value: object) -> bool:
        return isinstance(value, ContinuousNote)

    def __str__(self) -> str:
        return CONTINUE_TOKEN

    def __repr__(self) -> str:
        return "ContinueNote()"

    def __gt__(self, value: object) -> bool:
        # greater than any notes
        return True

    def copy(self) -> "ContinuousNote":
        return ContinuousNote()

    def __hash__(self) -> int:
        return hash("ContinueNote")

    def standardized_str(self) -> str:
        return CONTINUE_TOKEN


class SingleNote(BasicNote):
    """A class representing a single chart note."""

    token: ChartNotation

    def __init__(self, token: ChartNotation) -> None:
        self.token = token

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, SingleNote):
            return False
        return self.token == value.token

    def __str__(self) -> str:
        return token_to_keyboard(self.token) or ""
    
    @property
    def keyboard(self) -> str | None:
        return token_to_keyboard(self.token)

    def __repr__(self) -> str:
        return f"SingleNote(token={self.token})"

    def __gt__(self, value: object) -> bool:
        if isinstance(value, ContinuousNote):
            return False
        if isinstance(value, SingleNote):
            return token_to_index(self.token) > token_to_index(value.token)
        return True  # greater than any notes

    def copy(self) -> "SingleNote":
        return SingleNote(self.token)

    def __hash__(self) -> int:
        return hash(self.token)

    def standardized_str(self) -> str:
        return str(self.token)


class ChordNote(BasicNote):
    """A class representing a chord chart note."""

    notes: list[BasicNote]

    def __init__(self, notes: list[BasicNote]) -> None:
        self.notes = [note.copy() for note in notes]

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ChordNote):
            return False
        return all((a == b for a, b in zip(self.notes, value.notes)))

    def __str__(self) -> str:
        return "(" + "".join(str(note) for note in self.notes) + ")"

    def __repr__(self) -> str:
        return f"ChordNote(notes={self.notes!r})"

    def __gt__(self, value: object) -> bool:
        # less than SingleNote
        if isinstance(value, SingleNote):
            return False

        if isinstance(value, ChordNote):
            # this should never happen in practice
            raise NotImplementedError(
                "Comparison between two ChordNotes is not supported."
            )

        return True

    def copy(self) -> "ChordNote":
        return ChordNote(self.notes)

    def __hash__(self) -> int:
        return hash(tuple(self.notes))

    def standardized_str(self) -> str:
        return (
            "(" + "".join(note.standardized_str() for note in sorted(self.notes)) + ")"
        )


class ArpeggioNote(BasicNote):
    """A class representing an arpeggio chart note."""

    notes: list[BasicNote]

    def __init__(self, notes: list[BasicNote]) -> None:
        self.notes = [note.copy() for note in notes]

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, ArpeggioNote):
            return False
        return all((a == b for a, b in zip(self.notes, value.notes)))

    def __str__(self) -> str:
        return "[" + "".join(str(note) for note in self.notes) + "]"

    def __repr__(self) -> str:
        return f"ArpeggioNote(notes={self.notes!r})"

    def __gt__(self, value: object) -> bool:
        # less than SingleNote and ChordNote
        if isinstance(value, (SingleNote, ChordNote)):
            return False

        if isinstance(value, ArpeggioNote):
            # this should never happen in practice
            raise NotImplementedError(
                "Comparison between two ArpeggioNotes is not supported."
            )

        return True

    def copy(self) -> "ArpeggioNote":
        return ArpeggioNote(self.notes)

    def __hash__(self) -> int:
        return hash(tuple(self.notes))

    def standardized_str(self) -> str:
        return "[" + "".join(note.standardized_str() for note in self.notes) + "]"


class TupletNote(BasicNote):
    """A class representing a tuplet chart note."""

    notes: list[BasicNote]

    def __init__(self, notes: list[BasicNote]) -> None:
        self.notes = [note.copy() for note in notes]

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, TupletNote):
            return False
        return all((a == b for a, b in zip(self.notes, value.notes)))

    def __str__(self) -> str:
        return "{" + "".join(str(note) for note in self.notes) + "}"

    def __repr__(self) -> str:
        return f"TupletNote(notes={self.notes!r})"

    def __gt__(self, value: object) -> bool:
        # less than SingleNote, ChordNote and ArpeggioNote
        if isinstance(value, (SingleNote, ChordNote, ArpeggioNote)):
            return False

        if isinstance(value, TupletNote):
            # this should never happen in practice
            raise NotImplementedError(
                "Comparison between two TupletNotes is not supported."
            )

        return True

    def copy(self) -> "TupletNote":
        return TupletNote(self.notes)

    def __hash__(self) -> int:
        return hash(tuple(self.notes))

    def standardized_str(self) -> str:
        return "{" + "".join(note.standardized_str() for note in self.notes) + "}"


class MutiNoteBuilder(ABC):
    """A builder class for creating multiple notes."""

    notes: list[BasicNote]

    def __init__(self) -> None:
        self.notes = []

    def add_note(self, note: BasicNote) -> None:
        self.notes.append(note)

    @abstractmethod
    def build(self) -> BasicNote:
        pass


class ChordBuilder(MutiNoteBuilder):
    """A builder class for creating chord notes."""

    def build(self) -> ChordNote:
        return ChordNote(self.notes)


class ArpeggioBuilder(MutiNoteBuilder):
    """A builder class for creating arpeggio notes."""

    def build(self) -> ArpeggioNote:
        return ArpeggioNote(self.notes)


class TupletBuilder(MutiNoteBuilder):
    """A builder class for creating tuplet notes."""

    def build(self) -> TupletNote:
        return TupletNote(self.notes)

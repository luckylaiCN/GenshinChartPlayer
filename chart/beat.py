from typing import Literal
from chart.constants import BracketTokenLeft
from chart.utils import (
    is_bracket_token,
    bracket_token_direction,
    is_keyboard_key,
    is_bracket_match,
    keyboard_to_token,
)
from chart.note import (
    BasicNote,
    ContinuousNote,
    SingleNote,
    ChordBuilder,
    TupletBuilder,
    MutiNoteBuilder,
    ArpeggioBuilder,
)


BeatUnit = BasicNote | Literal[" "]


class BeatParseError(Exception):
    def __init__(self, message: str, position: int) -> None:
        super().__init__(message)
        self.position = position


class Beat:
    """A class representing a beat in the chart.

    Attributes:
    notes: A list of BeatUnit objects representing the notes in the beat.
    raw_text: The raw text of the beat.
    line_number: int | None , available when parsing a full chart
    position: int | None , position in line, available when parsing a full chart
    """

    notes: list[BeatUnit]
    raw_text: str
    line_number: int | None  # available when parsing a full chart
    position: int | None  # position in line, available when parsing a full chart

    def __init__(self, raw_text: str) -> None:
        self.raw_text = raw_text
        self.notes = []

    def set_notes(self, notes: list[BeatUnit]) -> None:
        self.notes = notes

    def __str__(self) -> str:
        return self.raw_text

    def __repr__(self) -> str:
        return f"Beat(raw_text={self.raw_text!r}, notes={self.notes!r})"

    def set_position(self, line_number: int, position: int) -> None:
        self.line_number = line_number
        self.position = position

    @property
    def begin_str(self) -> str | None:
        if self.line_number is not None and self.position is not None:
            return f"{self.line_number}.{self.position}"  # tkinter text position format
        return None
    
    @property
    def end_str(self) -> str | None:
        if self.line_number is not None and self.position is not None:
            end_pos = self.position + len(self.raw_text)
            return f"{self.line_number}.{end_pos}"  # tkinter text position format
        return None

    @staticmethod
    def from_string(beat_str: str) -> "Beat":
        beat = Beat(beat_str)
        beat.parse()
        return beat

    def parse(self) -> None:
        builder_stack: list[MutiNoteBuilder] = []
        bracket_stack: list[BracketTokenLeft] = []
        notes: list[BeatUnit] = []
        for char_index, char in enumerate(self.raw_text):
            if is_bracket_token(char):
                direction = bracket_token_direction(char)  # type: ignore
                if direction == "left":
                    if char == "(":
                        builder_stack.append(ChordBuilder())
                    elif char == "{":
                        builder_stack.append(TupletBuilder())
                    elif char == "[":
                        builder_stack.append(ArpeggioBuilder())
                    else:
                        pass  # should never happen
                    bracket_stack.append(char)  # type: ignore

                elif direction == "right":
                    if not bracket_stack:
                        raise BeatParseError(
                            f"Unmatched closing bracket '{char}'", char_index
                        )
                    last_bracket = bracket_stack.pop()
                    if not is_bracket_match(last_bracket, char):  # type: ignore
                        raise BeatParseError(
                            f"Mismatched brackets: '{last_bracket}' and '{char}'",
                            char_index,
                        )

                    if not builder_stack:
                        raise BeatParseError(
                            f"No builder found for closing bracket '{char}'", char_index
                        )
                    completed_builder = builder_stack.pop()
                    completed_note = completed_builder.build()

                    if builder_stack:
                        builder_stack[-1].add_note(completed_note)
                    else:
                        notes.append(completed_note)
            else:
                if is_keyboard_key(char):
                    note = SingleNote(keyboard_to_token(char))  # type: ignore
                elif char == "_":
                    note = ContinuousNote()
                elif char == " ":
                    note = " "
                else:
                    raise BeatParseError(f"Invalid character '{char}'", char_index)

                if builder_stack:
                    if note != " ":
                        builder_stack[-1].add_note(note)
                else:
                    notes.append(note)

        if bracket_stack:
            raise BeatParseError(
                "Unclosed brackets at end of beat", len(self.raw_text) - 1
            )

        self.set_notes(notes)

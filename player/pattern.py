from chart.note import (
    SingleNote,
    ContinuousNote,
    BasicNote,
    ChordNote,
    ArpeggioNote,
    TupletNote,
)
from chart.beat import Beat
from player.interal import InternalProperty


class NoteContainerRelative:
    """A container for note with playtime and duration.
    Attributes:
    note: The BasicNote object.
    play_time: The time when the note should be played, in seconds.
    """

    note: SingleNote
    relative_play_time: float  # in seconds

    def __init__(self, note: SingleNote, relative_play_time: float) -> None:
        self.note = note
        self.relative_play_time = relative_play_time

    def __gt__(self, value: object) -> bool:
        if not isinstance(value, NoteContainerRelative):
            return NotImplemented
        if self.relative_play_time == value.relative_play_time:
            return self.note > value.note

        return self.relative_play_time > value.relative_play_time

    def __str__(self) -> str:
        return f"NoteContainerRelative(note={self.note}, relative_play_time={self.relative_play_time})"

    def __repr__(self) -> str:
        return f"NoteContainerRelative(note={self.note!r}, relative_play_time={self.relative_play_time})"


class NoteContainer:
    """A container for note with playtime and duration.
    Attributes:
    note: The BasicNote object.
    play_time: The time when the note should be played, in seconds.
    """

    note: SingleNote
    play_time: float  # in seconds

    def __init__(self, note: SingleNote, play_time: float) -> None:
        self.note = note
        self.play_time = play_time

    def __gt__(self, value: object) -> bool:
        if not isinstance(value, NoteContainer):
            return NotImplemented
        if self.play_time == value.play_time:
            return self.note > value.note

        return self.play_time > value.play_time

    def __str__(self) -> str:
        return f"NoteContainer(note={self.note}, play_time={self.play_time})"

    def __repr__(self) -> str:
        return f"NoteContainer(note={self.note!r}, play_time={self.play_time})"


class PatternMismatchWarning(Warning):
    def __init__(self, message: str, begin_str: str, end_str: str) -> None:
        super().__init__(message)
        self.begin_str = begin_str
        self.end_str = end_str


class PatternMismatchInfo:
    """
    Information about a pattern mismatch in the chart.
    Attributes:
    begin_str: The begin position string of the mismatch.
    end_str: The end position string of the mismatch.
    message: The warning message.
    """

    begin_str: str
    end_str: str
    message: str

    def __init__(self, begin_str: str, end_str: str, message: str) -> None:
        self.begin_str = begin_str
        self.end_str = end_str
        self.message = message


class PatternMismatchException(Warning):
    """
    Exception raised for pattern mismatches that occur during chart parsing.
    Attributes:
    warnings: A list of PatternMismatchInfo objects representing individual mismatch warnings.
    """

    warnings: list[PatternMismatchInfo]

    def __init__(self, warnings: list[PatternMismatchInfo]) -> None:
        super().__init__("Multiple pattern mismatches occurred.")
        self.warnings = warnings


def get_notes_patterns_in_multiple_cords(
    note: BasicNote, begin_time: float, full_duration: float, minimum_time_unit: float
) -> list[NoteContainerRelative]:
    result: list[NoteContainerRelative] = []
    if isinstance(note, SingleNote):
        result.append(NoteContainerRelative(note=note, relative_play_time=begin_time))
    elif isinstance(note, ChordNote):
        for sub_note in note.notes:
            sub_patterns = get_notes_patterns_in_multiple_cords(
                sub_note, begin_time, full_duration, minimum_time_unit
            )
            result.extend(sub_patterns)
    elif isinstance(note, ArpeggioNote):
        num_sub_notes = len(note.notes)
        if num_sub_notes == 0:
            return []
        sub_duration = minimum_time_unit / num_sub_notes * 0.5
        for index, sub_note in enumerate(note.notes):
            sub_begin_time = begin_time + index * sub_duration
            sub_patterns = get_notes_patterns_in_multiple_cords(
                sub_note, sub_begin_time, sub_duration, minimum_time_unit
            )
            result.extend(sub_patterns)
    elif isinstance(note, TupletNote):
        num_sub_notes = len(note.notes)
        if num_sub_notes == 0:
            return []
        sub_duration = full_duration / num_sub_notes
        for index, sub_note in enumerate(note.notes):
            sub_begin_time = begin_time + index * sub_duration
            sub_patterns = get_notes_patterns_in_multiple_cords(
                sub_note, sub_begin_time, sub_duration, minimum_time_unit
            )
            result.extend(sub_patterns)

    return sorted(result)


def get_notes_pattern_in_beat(
    beat: Beat, internal_property: InternalProperty
) -> list[NoteContainerRelative]:
    """Get the notes pattern for a given beat and internal properties.
    Args:
    beat: The Beat object.
    internal_property: The InternalProperty object.
    Returns:
    A list of NoteContainer objects representing the notes pattern.
    """
    full_duration = 60.0 / internal_property.bpm
    num_notes = len(beat.notes)
    target_notes = []
    if num_notes == 0:
        return []

    # check single note or empty note
    # if beat.notes[0] != " " and all(n == " " for n in beat.notes[1:]):
    #     notes = get_notes_patterns_in_multiple_cords(
    #         beat.notes[0], 0.0, full_duration, full_duration
    #     )
    #     return notes
    if all(n == " " for n in beat.notes):
        return []

    target_notes = beat.notes.copy()
    if (
        beat.notes[-1] == " "
    ):  # some chart editors add an extra space at the end to make editing easier
        if internal_property.time_signature == 4:
            if num_notes % 4 == 1 or num_notes == 3:
                target_notes = beat.notes[:-1]
                num_notes -= 1
        elif internal_property.time_signature == 3:
            if num_notes % 3 == 1:
                target_notes = beat.notes[:-1]
                num_notes -= 1

    if internal_property.time_signature == 4:
        if num_notes not in (1, 2, 4, 8, 16):
            raise PatternMismatchWarning(
                f"Number of notes {num_notes} in beat does not match 4/4 time signature.",
                beat.begin_str or "",
                beat.end_str or "",
            )
    elif internal_property.time_signature == 3:
        if num_notes not in (1, 3, 6, 12):
            raise PatternMismatchWarning(
                f"Number of notes {num_notes} in beat does not match 3/4 time signature.",
                beat.begin_str or "",
                beat.end_str or "",
            )

    minimum_time_unit = full_duration / num_notes
    note_containers: list[NoteContainerRelative] = []
    current_time = 0.0
    begin_time = 0.0
    current_duration = 0.0
    operating_note: BasicNote | None = None
    for note in target_notes:
        # " ", rest note; "_"(Continuous note) are treated as no note, but with duration
        if isinstance(note, ContinuousNote):
            if current_duration == 0.0:
                raise ValueError(
                    "Continuous note cannot appear without a preceding note."
                )
            current_duration += minimum_time_unit
        elif note == " ":
            current_time += minimum_time_unit
        else:
            if operating_note is not None:
                note_patterns = get_notes_patterns_in_multiple_cords(
                    operating_note, begin_time, current_duration, minimum_time_unit
                )
                note_containers.extend(note_patterns)
            begin_time = current_time
            operating_note = note
            current_time += minimum_time_unit
            current_duration = minimum_time_unit
    if operating_note is not None:
        note_patterns = get_notes_patterns_in_multiple_cords(
            operating_note, begin_time, current_duration, minimum_time_unit
        )
        note_containers.extend(note_patterns)
    return sorted(note_containers)

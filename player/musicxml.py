import music21

from fractions import Fraction

from chart.beat import Beat
from chart.note import (
    BasicNote,
    SingleNote,
    ContinuousNote,
    TupletNote,
    ChordNote,
    ArpeggioNote,
)


class DurationNoteContainer:
    note: BasicNote
    begin_time: Fraction
    duration: Fraction

    def __init__(
        self, note: BasicNote, begin_time: Fraction, duration: Fraction
    ) -> None:
        self.note = note
        self.begin_time = begin_time
        self.duration = duration

    def apply_to_stream(
        self, stream: music21.stream.Stream, base_begin_beat: int
    ) -> None:
        if isinstance(self.note, SingleNote):
            pitch = self.note.token
            music21_note = music21.note.Note(pitch)
            music21_note.duration.quarterLength = float(self.duration)
            stream.append(music21_note)
        elif isinstance(self.note, (ChordNote, ArpeggioNote)):
            # only support for all sub notes are single notes
            pitches = [
                sub_note.token
                for sub_note in self.note.notes
                if isinstance(sub_note, SingleNote)
            ]
            music21_chord = music21.chord.Chord(pitches)
            music21_chord.duration.quarterLength = float(self.duration)
            # add mark for arpeggio
            if isinstance(self.note, ArpeggioNote):
                arpeggio_mark = music21.expressions.ArpeggioMark("normal")
                music21_chord.expressions.append(arpeggio_mark)
            stream.append(music21_chord)
        elif isinstance(self.note, TupletNote):
            sub_notes = self.note.notes
            num_sub_notes = len(sub_notes)
            duration_per_sub_note = self.duration / num_sub_notes
            for sub_note in sub_notes:
                if isinstance(sub_note, SingleNote):
                    pitch = sub_note.token
                    music21_note = music21.note.Note(pitch)
                    music21_note.duration.quarterLength = float(duration_per_sub_note)
                    stream.append(music21_note)
                elif isinstance(sub_note, (ChordNote, ArpeggioNote)):
                    pitches = [
                        n.token for n in sub_note.notes if isinstance(n, SingleNote)
                    ]
                    music21_chord = music21.chord.Chord(pitches)
                    music21_chord.duration.quarterLength = float(duration_per_sub_note)
                    if isinstance(sub_note, ArpeggioNote):
                        arpeggio_mark = music21.expressions.ArpeggioMark("normal")
                        music21_chord.expressions.append(arpeggio_mark)
                    stream.append(music21_chord)
                else:
                    music21_rest = music21.note.Rest()
                    music21_rest.duration.quarterLength = float(duration_per_sub_note)
                    stream.append(music21_rest)
        else:
            raise NotImplementedError(f"Unsupported note type: {type(self.note)}")


def get_notes_partial_pattern_in_beat(beat: Beat) -> list[DurationNoteContainer]:
    """Convert the notes in a beat to a list of DurationNoteContainer objects."""

    notes = beat.notes
    num_notes = len(notes)
    if num_notes == 0:
        return []

    if all(n == " " for n in notes):
        return []

    if (beat.notes[-1] == " " and num_notes % 4 == 1) or (
        num_notes == 3 and beat.notes[-1] == " "
    ):
        notes = beat.notes[:-1]
        num_notes -= 1

    result_notes: list[BasicNote] = []
    begin_times: list[Fraction] = []
    durations: list[Fraction] = []
    min_duration = Fraction(1, num_notes)
    should_continue = True
    for index, note in enumerate(notes):
        if note == " ":
            should_continue = False
            continue

        if isinstance(note, (ContinuousNote)):
            if should_continue:
                durations[-1] += min_duration
            continue  # skip continue notes, they will be handled in the next step

        result_notes.append(note)
        begin_times.append(Fraction(index, num_notes))
        durations.append(min_duration)
        should_continue = True

    # override durations if note is not a tuplet note
    for index, note in enumerate(result_notes):
        if not isinstance(note, TupletNote):
            # let duration = next_begin_time - current_begin_time
            if index < len(result_notes) - 1:
                durations[index] = begin_times[index + 1] - begin_times[index]
            else:
                durations[index] = Fraction(1) - begin_times[index]

    note_containers: list[DurationNoteContainer] = []
    for note, begin_time, duration in zip(result_notes, begin_times, durations):
        note_containers.append(DurationNoteContainer(note, begin_time, duration))

    return note_containers

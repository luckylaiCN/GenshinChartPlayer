import math

import music21

from fractions import Fraction
from typing import Literal

from chart.beat import Beat
from chart.note import (
    BasicNote,
    SingleNote,
    ContinuousNote,
    TupletNote,
    ChordNote,
    ArpeggioNote,
)
from chart.builder import build_beat


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
            pitches = []
            for n in self.note.notes:
                if isinstance(n, SingleNote):
                    pitches.append(n.token)
                if isinstance(n, ChordNote):
                    for sub_n in n.notes:
                        if isinstance(sub_n, SingleNote):
                            pitches.append(sub_n.token)
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
                    pitches = []
                    for n in sub_note.notes:
                        if isinstance(n, SingleNote):
                            pitches.append(n.token)
                        if isinstance(n, ChordNote):
                            for sub_n in n.notes:
                                if isinstance(sub_n, SingleNote):
                                    pitches.append(sub_n.token)
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


def get_pitch_num(note: music21.note.Note) -> int:
    """Convert a music21 note to a MIDI pitch number."""
    return note.pitch.midi


def is_chord_arpeggio(chord: music21.chord.Chord) -> bool:
    """Check if a music21 chord has an arpeggio mark."""
    return any(
        isinstance(n, music21.expressions.ArpeggioMark) for n in chord.expressions
    )


def build_part_from_pitches_and_begin_times(
    pitches: list[tuple[list[int], Literal["Note", "Chord", "Arpeggio"]]],
    begin_times: list[Fraction],
    full_time: Fraction,
) -> music21.stream.Part:
    """Build a music21 part from a list of pitches and begin times.
    Fixes duration according to begin times between notes, and fills the rest with rests.
    """
    part = music21.stream.Part()

    if len(pitches) == 0:
        added_time = 0
        while added_time < full_time:
            rest = music21.note.Rest()
            rest.duration.quarterLength = float(min(full_time - added_time, 4))
            added_time += min(full_time - added_time, 4)
            part.append(rest)
        return part

    # add duration before the first note if the first note does not start at the beginning of the beat
    if begin_times[0] > 0:
        added_time = 0
        while added_time < begin_times[0]:
            rest = music21.note.Rest()
            rest.duration.quarterLength = float(min(begin_times[0] - added_time, 4))
            added_time += min(begin_times[0] - added_time, 4)
            part.append(rest)

    # default duration is 4 beats, which is the whole beat, will be fixed later according to begin times between notes
    index = 0
    while index < len(pitches):
        current_pitches, current_type = pitches[index]
        current_time = begin_times[index]
        next_time = begin_times[index + 1] if index < len(pitches) - 1 else full_time
        fix_duration = 4
        # if it is not a /1 /2 /4 /8 ... /64 begin time, the est duration should be the nearest measure end
        if is_tuplet_time(current_time):
            est_next_time = current_time // 4 * 4 + 4
            est_next_time = min(est_next_time, full_time)
            fix_duration = est_next_time - current_time
        est_duration = next_time - current_time
        duration = min(est_duration, fix_duration)
        is_duartion_covered = est_duration == duration
        if current_type == "Note":
            music21_note = music21.note.Note(current_pitches[0])
            music21_note.duration.quarterLength = duration
            # remove accidental if the pitch is natural
            if (
                music21_note.pitch.accidental is not None
                and music21_note.pitch.accidental.name == "natural"
            ):
                music21_note.pitch.accidental = None
            part.append(music21_note)
        elif current_type == "Chord":
            music21_chord = music21.chord.Chord(current_pitches)
            music21_chord.duration.quarterLength = duration
            # remove accidental if the pitch is natural
            for note in music21_chord.notes:
                if (
                    note.pitch.accidental is not None
                    and note.pitch.accidental.name == "natural"
                ):
                    note.pitch.accidental = None

            part.append(music21_chord)
        elif current_type == "Arpeggio":
            music21_chord = music21.chord.Chord(current_pitches)
            music21_chord.duration.quarterLength = duration
            arpeggio_mark = music21.expressions.ArpeggioMark("normal")
            # remove accidental if the pitch is natural
            for note in music21_chord.notes:
                if (
                    note.pitch.accidental is not None
                    and note.pitch.accidental.name == "natural"
                ):
                    note.pitch.accidental = None
            music21_chord.expressions.append(arpeggio_mark)
            part.append(music21_chord)
        if not is_duartion_covered:
            added_time = 0
            while added_time < est_duration - duration:
                rest = music21.note.Rest()
                rest.duration.quarterLength = float(
                    min(est_duration - duration - added_time, 4)
                )
                added_time += min(est_duration - duration - added_time, 4)
                part.append(rest)

        index += 1

    return part


def melody_chord_split(pitches: list[int]) -> tuple[list[int], list[int]]:
    """Split a list of pitches into a melody pitch and a chord pitch according to the distance between pitches."""

    if len(pitches) == 1:
        return pitches, []

    highest_pitch = max(pitches)
    lowest_pitch = min(pitches)

    if highest_pitch - lowest_pitch < 8:
        return pitches, []

    melodies = []
    chords = []
    for pitch in pitches:
        if abs(pitch - highest_pitch) < abs(pitch - lowest_pitch):
            melodies.append(pitch)
        else:
            chords.append(pitch)
    return melodies, chords


def is_tuplet_time(duration: Fraction) -> bool:
    """Check if the given duration is a tuplet duration."""
    standard_denominators = [1, 2, 4, 8, 16, 32, 64]
    return duration.denominator not in standard_denominators


def divide_into_melody_and_chords(
    stream: music21.stream.Stream,
) -> music21.stream.Stream:
    """Divide a music21 stream into a melody stream and a chord stream."""
    result_stream = music21.stream.Stream()

    melody_tolerance = 10  # minor seventh
    chord_tolerance = 9  # major sixth

    melody_degree_tolerance_pitch = get_pitch_num(music21.note.Note("B4"))

    current_pitch = 0

    tempo_indexs: list[tuple[Fraction, float]] = []
    note_begin_times: list[Fraction] = []
    note_pitches: list[int] = []
    notes: list[music21.note.Note | music21.chord.Chord] = []

    melody_indexes: list[int] = []

    full_time = stream.highestTime

    for element in stream.recurse():
        if isinstance(element, music21.tempo.MetronomeMark):
            tempo_indexs.append(
                (Fraction(element.offset).limit_denominator(64), element.number)
            )
        elif isinstance(element, (music21.note.Note, music21.chord.Chord)):
            note_begin_times.append(Fraction(element.offset).limit_denominator(64))
            if isinstance(element, music21.note.Note):
                pitch_num = get_pitch_num(element)
                note_pitches.append(pitch_num)
                notes.append(element)
            else:  # chord
                pitch_num = max(get_pitch_num(n) for n in element.notes)
                note_pitches.append(pitch_num)
                notes.append(element)

    if len(notes) < 2:
        return stream

    # first_pitch, second_pitch = note_pitches[0], note_pitches[1]

    # determine if the first note or the second note is the melody note based on the pitch difference

    note_index = 0
    # melody_begin_index = 0

    # if second_pitch - first_pitch >= chord_tolerance:
    #     melody_begin_index = 1 # the second note is the melody note

    # melody_indexes.append(melody_begin_index)
    # note_index = melody_begin_index + 1

    # the codes above is merged into the while loop below.

    last_is_melody = False
    note_process_length = len(notes) - 1
    recent_notes_pitches: list[int] = []
    while note_index < note_process_length:
        current_pitch = note_pitches[note_index]
        next_pitch = note_pitches[note_index + 1]
        diff = next_pitch - current_pitch

        duration = notes[note_index].duration.quarterLength
        fraction_division = Fraction(duration).limit_denominator(64)
        if is_tuplet_time(fraction_division):
            # if the duration is not a standard duration, consider it as a tuplet note,
            # keep the same melody/chord status as the last note, and skip the duration check for this note.
            if last_is_melody:
                melody_indexes.append(note_index)
            note_index += 1
            continue

        last_is_melody = True

        # recent_notes_pitches are note pitches that are distance < 8 beats in the melody.
        recent_notes_pitches = []
        for index in range(len(melody_indexes) - 1, -1, -1):
            if (
                note_begin_times[note_index] - note_begin_times[melody_indexes[index]]
                < 8
            ):
                recent_notes_pitches.append(note_pitches[melody_indexes[index]])
            else:
                break

        if recent_notes_pitches:
            average_recent_pitch = sum(recent_notes_pitches) / len(recent_notes_pitches)
            avergae_diff = average_recent_pitch - current_pitch

            if avergae_diff <= melody_tolerance:
                if note_pitches[melody_indexes[-1]] - current_pitch < chord_tolerance:
                    melody_indexes.append(note_index)
                    note_index += 1
                    continue
                elif abs(diff) < chord_tolerance and (
                    current_pitch >= melody_degree_tolerance_pitch
                ):
                    melody_indexes.append(note_index)
                    note_index += 1
                    continue
            else:
                if (diff < chord_tolerance) and all(
                    note_pitches[i] - current_pitch < chord_tolerance
                    for i in melody_indexes[-2:]
                ):
                    melody_indexes.append(note_index)
                    note_index += 1
                    continue
                elif (
                    (abs(diff) < chord_tolerance)
                    and (current_pitch >= melody_degree_tolerance_pitch)
                    and all(
                        note_pitches[i] - current_pitch < chord_tolerance
                        for i in melody_indexes[-2:]
                    )
                ):
                    melody_indexes.append(note_index)
                    note_index += 1
                    continue

        else:
            # consider as a new beginning of a melody, clear the recent_notes_pitches
            # decide according to the pitch difference between the current note and the next note
            if diff >= chord_tolerance:
                melody_indexes.append(note_index + 1)
                note_index += 2
                continue
            else:
                melody_indexes.append(note_index)
                note_index += 1
                continue
        last_is_melody = False
        note_index += 1

    if note_index < len(notes):
        # check last note
        recent_notes_pitches = []
        for index in range(len(melody_indexes) - 1, -1, -1):
            if note_begin_times[-1] - note_begin_times[melody_indexes[index]] < 8:
                recent_notes_pitches.append(note_pitches[melody_indexes[index]])
            else:
                break

        if recent_notes_pitches:
            average_recent_pitch = sum(recent_notes_pitches) / len(recent_notes_pitches)
            avergae_diff = average_recent_pitch - current_pitch
            if avergae_diff <= melody_tolerance:
                if note_pitches[melody_indexes[-1]] - current_pitch < chord_tolerance:
                    melody_indexes.append(note_index)
                    note_index += 1

    # filter out the melody notes and chord notes
    melody_pitches: list[tuple[list[int], Literal["Note", "Chord", "Arpeggio"]]] = []
    chord_pitches: list[tuple[list[int], Literal["Note", "Chord", "Arpeggio"]]] = []

    melody_begin_times: list[Fraction] = []
    chord_begin_times: list[Fraction] = []

    melody_index_set = set(melody_indexes)

    for index, note in enumerate(notes):
        if index in melody_index_set:
            if isinstance(note, music21.note.Note):
                melody_pitches.append(([get_pitch_num(note)], "Note"))
            elif isinstance(note, music21.chord.Chord):
                is_arpeggio = is_chord_arpeggio(note)
                # select all pitches that are in chord distance

                # if some durations are tuplet, do not split melody and chord, consider all pitches as melody.
                # however it is acceptable for the first note of a tuplet.
                if is_tuplet_time(
                    Fraction(note.duration.quarterLength).limit_denominator(64)
                ) and is_tuplet_time(
                    Fraction(note.offset - int(note.offset)).limit_denominator(64)
                ):
                    melody_pitches.append(
                        ([get_pitch_num(n) for n in note.notes], "Chord")
                    )
                    melody_begin_times.append(note_begin_times[index])
                    continue

                in_chords, out_chords = melody_chord_split(
                    [get_pitch_num(n) for n in note.notes]
                )

                # let in_chords to be in the melody.
                if in_chords:
                    if len(in_chords) == 1:
                        melody_pitches.append((in_chords, "Note"))
                    else:
                        if is_arpeggio:
                            melody_pitches.append((in_chords, "Arpeggio"))
                        else:
                            melody_pitches.append((in_chords, "Chord"))
                if out_chords:
                    if len(out_chords) == 1:
                        chord_pitches.append((out_chords, "Note"))
                    else:
                        if is_arpeggio:
                            chord_pitches.append((out_chords, "Arpeggio"))
                        else:
                            chord_pitches.append((out_chords, "Chord"))

                    chord_begin_times.append(note_begin_times[index])

            melody_begin_times.append(note_begin_times[index])
        else:
            if isinstance(note, music21.note.Note):
                chord_pitches.append(([get_pitch_num(note)], "Note"))
            else:
                if is_chord_arpeggio(note):
                    chord_pitches.append(
                        ([get_pitch_num(n) for n in note.notes], "Arpeggio")
                    )
                else:
                    chord_pitches.append(
                        ([get_pitch_num(n) for n in note.notes], "Chord")
                    )
            chord_begin_times.append(note_begin_times[index])

    melody_part = build_part_from_pitches_and_begin_times(
        melody_pitches,
        melody_begin_times,
        full_time=Fraction(full_time).limit_denominator(64),
    )
    chord_part = build_part_from_pitches_and_begin_times(
        chord_pitches,
        chord_begin_times,
        full_time=Fraction(full_time).limit_denominator(64),
    )

    # recover tempo markings
    for tempo_time, tempo in tempo_indexs:
        tempo_mark = music21.tempo.MetronomeMark(number=tempo)
        melody_part.insert(tempo_time, tempo_mark)

    result_stream.insert(0, melody_part)
    result_stream.insert(0, chord_part)

    return result_stream


def convert_musicxml_stream_to_pitches_and_begin_times(
    stream: music21.stream.Stream,
) -> tuple[
    list[tuple[list[int], Literal["Note", "Chord", "Arpeggio"]]],
    list[Fraction],
    list[tuple[int, float]],
]:
    """Convert a music21 stream to a list of pitches and begin times."""
    pitches: list[tuple[list[int], Literal["Note", "Chord", "Arpeggio"]]] = []
    begin_times: list[Fraction] = []
    tempo_indexs: list[tuple[int, float]] = []

    flattened_stream = stream.flatten().recurse()
    for element in flattened_stream:
        # tempo markings
        if isinstance(element, music21.tempo.MetronomeMark):
            tempo_indexs.append((int(element.offset), element.number))
            continue

        if isinstance(element, (music21.note.Note, music21.chord.Chord)):
            if element.tie is not None and element.tie.type in ("stop", "continue"):
                # if the note is tied from the previous note, skip it, as it will be handled in the next step when processing the previous note.
                continue
            curr_time = Fraction(element.offset).limit_denominator(64)
            if len(begin_times):
                pre_time = begin_times[-1]
                if curr_time < pre_time:
                    # this should not happen, but just in case, if the current time is smaller than the previous time, consider it as a continuation of the previous note, and do not add it to the pitches and begin_times.
                    continue
                if curr_time == pre_time:
                    # merge the current note with the previous note, consider them as a chord if they are not already a chord.
                    # if any of the two notes is an arpeggio, consider the merged note as an arpeggio.
                    pre_pitches, pre_type = pitches[-1]
                    if isinstance(element, music21.note.Note):
                        curr_pitches = [get_pitch_num(element)]
                        curr_type = "Note"
                    else:
                        curr_pitches = [get_pitch_num(n) for n in element.notes]
                        if is_chord_arpeggio(element):
                            curr_type = "Arpeggio"
                        else:
                            curr_type = "Chord"
                    merged_pitches = list(set(pre_pitches) | set(curr_pitches))
                    if pre_type == "Arpeggio" or curr_type == "Arpeggio":
                        merged_type = "Arpeggio"
                    elif pre_type == "Chord" or curr_type == "Chord":
                        merged_type = "Chord"
                    elif len(merged_pitches) > 1:
                        merged_type = "Chord"
                    else:
                        merged_type = "Note"  # should not happen.
                    pitches[-1] = (merged_pitches, merged_type)
                    continue

            if isinstance(element, music21.note.Note):
                pitches.append(([get_pitch_num(element)], "Note"))
            else:
                if is_chord_arpeggio(element):
                    pitches.append(
                        ([get_pitch_num(n) for n in element.notes], "Arpeggio")
                    )
                else:
                    pitches.append(([get_pitch_num(n) for n in element.notes], "Chord"))
            begin_times.append(curr_time)

    return pitches, begin_times, tempo_indexs


def convert_musicxml_stream_to_chart_str(stream: music21.stream.Stream) -> str:
    """Convert a music21 stream to a chart string."""

    full_time = stream.highestTime
    max_beat_num = math.ceil(full_time)
    pitches, begin_times, tempo_indexes = (
        convert_musicxml_stream_to_pitches_and_begin_times(stream)
    )
    if len(pitches) == 0:
        return ""
    if len(pitches) != len(begin_times):
        raise ValueError("Length of pitches and begin_times must be the same.")
    if not tempo_indexes:
        tempo_indexes = [(0, 120.0)]  # default tempo is 120 BPM
    if tempo_indexes[0][0] != 0:
        tempo_indexes.insert(
            0, (0, 120.0)
        )  # add default tempo at the beginning if not exist

    beat_str: list[str] = ["    "] * max_beat_num
    beat_pitches_batch: list[
        tuple[list[int], Literal["Note", "Chord", "Arpeggio"]]
    ] = []
    beat_begin_times_batch: list[Fraction] = []
    working_beat_index = 0
    for pitch, begin_time in zip(pitches, begin_times):
        beat_num = int(begin_time)
        if working_beat_index == beat_num:
            beat_pitches_batch.append(pitch)
            beat_begin_times_batch.append(begin_time - beat_num)
        else:
            beat_str[working_beat_index] = build_beat(
                beat_pitches_batch, beat_begin_times_batch
            )
            working_beat_index = beat_num
            beat_pitches_batch = [pitch]
            beat_begin_times_batch = [begin_time - beat_num]
        working_beat_index = beat_num
    if beat_pitches_batch:
        beat_str[working_beat_index] = build_beat(
            beat_pitches_batch, beat_begin_times_batch
        )

    # each line 4 beats
    # every 4 lines a section, add empty line
    beat_counter = 0
    line_counter = 0
    line_container: list[str] = []
    chart_lines: list[str] = []
    for beat_index in range(max_beat_num):
        # check if there is a tempo change at the current beat, if so, add a tempo marking line before the current beat line
        if tempo_indexes and tempo_indexes[0][0] == beat_index:
            tempo = tempo_indexes[0][1]

            tempo_indexes.pop(0)
            beat_counter = 0
            line_counter = 0
            if line_container:
                chart_lines.append("/".join(line_container) + "/\n")
                line_container = []
            if len(chart_lines) > 0:
                chart_lines.append("\n")
            chart_lines.append(f"@set bpm {tempo}\n")

        line_container.append(beat_str[beat_index])
        beat_counter += 1
        if beat_counter == 4:
            chart_lines.append("/".join(line_container) + "/\n")
            line_container = []
            beat_counter = 0
            line_counter += 1
            if line_counter == 4:
                chart_lines.append("\n")
                line_counter = 0

    if line_container:
        chart_lines.append("/".join(line_container) + "/\n")

    return "".join(chart_lines)

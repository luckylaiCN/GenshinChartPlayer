from typing import Literal
from fractions import Fraction
from chart.utils import pitch_to_keyboard
from shared.utils import lcm_n


def get_string_name(
    pitches: list[int],
    pitch_type: Literal["Note", "Chord", "Arpeggio"],
    length: int,
    space: str = " ",
    error: Literal["raise", "ignore"] = "ignore",
) -> str:
    """Get the string representation of a list of pitches based on their type."""
    append_space = space * (length - 1)
    if pitch_type == "Note":
        if len(pitches) != 1:
            if error == "raise":
                raise ValueError("A Note type must have exactly one pitch.")
            elif error == "ignore":
                return space * length
        keyboard_key = pitch_to_keyboard(pitches[0])
        if keyboard_key is None:
            if error == "raise":
                raise ValueError(f"Invalid pitch number: {pitches[0]}")
            elif error == "ignore":
                return space * length
        return keyboard_key + append_space
    elif pitch_type in ["Chord", "Arpeggio"]:
        keyboard_keys = []
        pitches = sorted(pitches)
        for pitch in pitches:
            keyboard_key = pitch_to_keyboard(pitch)
            if keyboard_key is None:
                if error == "raise":
                    raise ValueError(f"Invalid pitch number: {pitch}")
            else:
                keyboard_keys.append(keyboard_key)
        if len(keyboard_keys) == 0:
            return space * length
        if pitch_type == "Chord":
            return "(" + "".join(keyboard_keys) + ")" + append_space
        elif pitch_type == "Arpeggio":
            return "[" + "".join(keyboard_keys) + "]" + append_space
    else:
        if error == "raise":
            raise ValueError(f"Invalid pitch type: {pitch_type}")
        else:
            return space * length


def build_beat(
    pitches: list[tuple[list[int], Literal["Note", "Chord", "Arpeggio"]]],
    begin_times: list[Fraction],
) -> str:
    """Build a beat string from a list of pitches and their types."""

    if len(pitches) != len(begin_times):
        raise ValueError("Length of pitches and begin_times must be the same.")

    if len(pitches) == 0:
        return ""

    slice_denominators = [1, 2, 4, 8, 16, 32, 64]
    tuplet_scopes: list[
        tuple[Fraction, Fraction]
    ] = []  # list of (begin_time, end_time) for each tuplet section
    is_in_tuplet = [False] * len(pitches)
    is_tuplet_begin = [False] * len(pitches)
    is_tuplet_end = [False] * len(pitches)
    tuplet_closed = True
    t_begin = Fraction(0)
    for i, this_begin_time in enumerate(begin_times):
        if this_begin_time.denominator not in slice_denominators:
            if tuplet_closed:
                if i > 0:
                    is_in_tuplet[i - 1] = True
                    t_begin = begin_times[i - 1]
                    is_tuplet_begin[i - 1] = True
                else:
                    t_begin = Fraction(0)
                    is_tuplet_begin[i] = True
            is_in_tuplet[i] = True
            tuplet_closed = False
        elif i > 0 and is_in_tuplet[i - 1]:
            t_end = this_begin_time
            if t_begin < t_end:
                tuplet_scopes.append((t_begin, t_end))
                is_tuplet_end[i - 1] = True
            t_begin = Fraction(0)
            t_end = Fraction(0)
            is_in_tuplet[i] = False
            tuplet_closed = True
    if is_in_tuplet[-1]:
        t_end = Fraction(1)
        if t_begin < t_end:
            tuplet_scopes.append((t_begin, t_end))
        is_tuplet_end[-1] = True

    part_strings: list[str] = []
    part_durations: list[Fraction] = []

    # get duration info
    tuplet_index = 0
    index = 0
    parts_num = 0
    while index < len(pitches):
        begin_time = begin_times[index]
        end_time = Fraction(1)
        if index < len(pitches) - 1:
            end_time = begin_times[index + 1]
        else:
            end_time = Fraction(1)
        duration = end_time - begin_time
        if is_in_tuplet[index]:
            tuplet_scope = tuplet_scopes[tuplet_index]
            tuplet_duration = tuplet_scope[1] - tuplet_scope[0]
            if tuplet_duration <= 0:
                raise ValueError("Invalid tuplet scope with non-positive duration.")
            while index < len(pitches) and not is_tuplet_end[index]:
                index += 1
            tuplet_index += 1
            duration = tuplet_duration
        index += 1
        part_durations.append(duration)
        parts_num += 1
    min_duration = min(part_durations)

    # check if all durations are tuplet.
    all_tuplet = False
    total_tuplet_duration = sum(end - begin for begin, end in tuplet_scopes)
    if total_tuplet_duration == Fraction(1):
        all_tuplet = True
        min_duration = min(min_duration, 1)
    else:
        min_duration = min(min_duration, Fraction(1, 4))
    index = 0
    tuplet_index = 0
    while index < len(pitches):
        pitch, pitch_type = pitches[index]
        duration = part_durations[len(part_strings)]
        if duration <= 0:
            raise ValueError("Begin times must be in ascending order and less than 1.")

        if is_in_tuplet[index]:
            pre_begin_time = tuplet_scopes[tuplet_index][0]
            tuplet_key_begin_time = begin_times[index]
            tuplet_scope = tuplet_scopes[tuplet_index]
            tuplet_duration = tuplet_scope[1] - tuplet_scope[0]
            if tuplet_duration <= 0:
                raise ValueError("Invalid tuplet scope with non-positive duration.")
            relative_tuplet_durations: list[Fraction] = []
            t_notes: list[tuple[list[int], Literal["Note", "Chord", "Arpeggio"]]] = []
            while True:
                this_begin_time = begin_times[index]
                t_notes.append(pitches[index])
                if is_tuplet_end[index]:
                    next_time = (
                        Fraction(1)
                        if index == len(pitches) - 1
                        else begin_times[index + 1]
                    )
                    relative_tuplet_durations.append(
                        (next_time - this_begin_time) / tuplet_duration
                    )
                    break
                else:
                    relative_tuplet_durations.append(
                        (begin_times[index + 1] - this_begin_time) / tuplet_duration
                    )
                index += 1

            # get lcm of denominators of relative_tuplet_durations
            denominators = [d.denominator for d in relative_tuplet_durations]
            numerators = [d.numerator for d in relative_tuplet_durations]
            lcm_denominator = lcm_n(denominators)
            scaled_numerators = [
                n * (lcm_denominator // d) for n, d in zip(numerators, denominators)
            ]
            note_strings = [
                get_string_name(p, t, length=scaled_n, space=" _")
                for (p, t), scaled_n in zip(t_notes, scaled_numerators)
            ]
            for i in range(int((tuplet_key_begin_time - pre_begin_time) / tuplet_duration * lcm_denominator)):
                note_strings.insert(0, "_")
            if all_tuplet:
                part_string = "{ " + " ".join(note_strings) + " }"
            else:
                part_string = "{" + "".join(note_strings) + "}"
            relative_length = int(tuplet_duration / min_duration)
            part_string += "_" * (relative_length - 1)
            part_strings.append(part_string)
            tuplet_index += 1
            index += 1  # move to the next note after the tuplet section
        else:
            part_string = get_string_name(pitch, pitch_type, length=1)
            part_string += " " * (int(duration / min_duration) - 1)
            part_strings.append(part_string)
            index += 1

    result = "".join(part_strings)
    if all(duration == min_duration for duration in part_durations) and len(tuplet_scopes) == 0:
        result += " "
    start_t = begin_times[0]
    if start_t > 0:
        result = " " * int(start_t / min_duration) + result
    return result

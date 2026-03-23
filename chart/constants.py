from typing import Literal

ChartNotation = Literal[
    "C3",
    "D3",
    "E3",
    "F3",
    "G3",
    "A3",
    "B3",
    "C4",
    "D4",
    "E4",
    "F4",
    "G4",
    "A4",
    "B4",
    "C5",
    "D5",
    "E5",
    "F5",
    "G5",
    "A5",
    "B5",
]
NOTATION_INDEX_TABLE: list[ChartNotation] = [
    "C3",
    "D3",
    "E3",
    "F3",
    "G3",
    "A3",
    "B3",
    "C4",
    "D4",
    "E4",
    "F4",
    "G4",
    "A4",
    "B4",
    "C5",
    "D5",
    "E5",
    "F5",
    "G5",
    "A5",
    "B5",
]

ChartKey = Literal[
    "Z",
    "X",
    "C",
    "V",
    "B",
    "N",
    "M",
    "A",
    "S",
    "D",
    "F",
    "G",
    "H",
    "J",
    "Q",
    "W",
    "E",
    "R",
    "T",
    "Y",
    "U",
]

KEYBOARD_INDEX_TABLE: list[ChartKey] = [
    "Z",
    "X",
    "C",
    "V",
    "B",
    "N",
    "M",
    "A",
    "S",
    "D",
    "F",
    "G",
    "H",
    "J",
    "Q",
    "W",
    "E",
    "R",
    "T",
    "Y",
    "U",
]

PITCH_NUM_TABLE = [
    48,  # C3
    50,  # D3
    52,  # E3
    53,  # F3
    55,  # G3
    57,  # A3
    59,  # B3
    60,  # C4
    62,  # D4
    64,  # E4
    65,  # F4
    67,  # G4
    69,  # A4
    71,  # B4
    72,  # C5
    74,  # D5
    76,  # E5
    77,  # F5
    79,  # G5
    81,  # A5
    83,  # B5
]

NUMERAL_NOTATION_TABLE = [
    "-1",
    "-2",
    "-3",
    "-4",
    "-5",
    "-6",
    "-7",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "+1",
    "+2",
    "+3",
    "+4",
    "+5",
    "+6",
    "+7",
]

CHORD_BRACKET_TOKENS = ("(", ")")

ARPPEGIO_BRACKET_TOKENS = ("[", "]")

TUPLET_BRACKET_TOKENS = ("{", "}")

BracketToken = Literal["(", ")", "[", "]", "{", "}"]
BracketTokenLeft = Literal["(", "[", "{"]
BracketTokenRight = Literal[")", "]", "}"]

BEAT_TOKEN = "/"

CONTINUE_TOKEN = "_"

SPACE_TOKEN = " "

ChartToken = ChartKey | Literal["/", "_", " "] | BracketToken

ALLOWED_TOKENS: list[ChartToken] = []
ALLOWED_TOKENS.extend(KEYBOARD_INDEX_TABLE)
ALLOWED_TOKENS.extend(CHORD_BRACKET_TOKENS)
ALLOWED_TOKENS.extend(ARPPEGIO_BRACKET_TOKENS)
ALLOWED_TOKENS.extend(TUPLET_BRACKET_TOKENS)
ALLOWED_TOKENS.append(BEAT_TOKEN)
ALLOWED_TOKENS.append(CONTINUE_TOKEN)
ALLOWED_TOKENS.append(SPACE_TOKEN)

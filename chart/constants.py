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

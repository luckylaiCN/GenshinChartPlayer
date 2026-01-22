import os

MAX_DICTORY_ENTRIES = 1000
ACCEPTED_FILE_EXTENSIONS = [".txt"]
EDITOR_FONT_FAMILY = "Consolas"  # we recommend using a monospace font
IS_DEBUG_MODE = os.getenv("GCP_DEBUG_MODE", "0") == "1"
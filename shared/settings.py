import os

from shared.utils import rpath

MAX_DICTORY_ENTRIES = 1000
ACCEPTED_FILE_EXTENSIONS = [".txt"]
EDITOR_FONT_FAMILY = "Consolas"  # we recommend using a monospace font
IS_DEBUG_MODE = os.getenv("GCP_DEBUG_MODE", "0") == "1"

# PATHS

# NOTE: preferably use current working directory, I don't want to pollute user folders
SESSION_FILE_PATH = rpath(".session.json")

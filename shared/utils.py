import os
import sys

PROJECT_ROOT: str

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS'.
    PROJECT_ROOT = sys._MEIPASS  # type: ignore
    PROJECT_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))
else:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))  # type: ignore
    PROJECT_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))

def rpath(*paths: str) -> str:
    """Get the absolute path relative to the project root."""
    return os.path.join(PROJECT_ROOT, *paths)

AUDIO_DIR = rpath("audio")
import os
import sys
import subprocess
import tkinter as tk
import inspect

import customtkinter as ctk

from tkinter import filedialog

from shared.settings import IS_DEBUG_MODE


def get_root_widget(widget: ctk.CTkBaseClass) -> ctk.CTk:
    """Recursively get the root widget (the main application window) from any widget."""
    parent = widget.master
    if parent is None:
        return widget  # type: ignore
    return get_root_widget(parent)  # type: ignore


def ask_open_folder_dialog() -> str | None:
    """Open a folder selection dialog and return the selected path."""

    root = tk.Tk()
    root.withdraw()  # Hide the root window
    folder_path = filedialog.askdirectory()
    root.destroy()  # Destroy the root window
    if folder_path:
        return os.path.abspath(folder_path)
    return None


def ask_open_file_dialog(exts: list[str]) -> str | None:
    """Open a file selection dialog and return the selected file path."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.askopenfilename(filetypes=[("Supported Files", exts)])
    root.destroy()  # Destroy the root window
    if len(file_path) == 0:
        file_path = None

    if file_path:
        return os.path.abspath(file_path)
    return None


def ask_save_file_dialog(exts: list[str], default_filename: str = "") -> str | None:
    """Open a save file dialog and return the selected file path."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.asksaveasfilename(
        defaultextension=exts[0],
        filetypes=[("Supported Files", exts)],
        initialfile=default_filename,
    )
    root.destroy()
    if len(file_path) == 0:
        return None
    if "." not in file_path and len(exts) > 0:
        file_path += exts[0]
    if file_path:
        return os.path.abspath(file_path)
    return None


def show_file_in_explorer(file_path: str) -> None:
    """Open the system file explorer and show the specified file.
    On Windows and macOS, this will attempt to select/highlight the file.
    On other platforms (for example, many Linux desktop environments), this
    may only open the containing directory.
    """
    if os.path.exists(file_path):
        if os.name == "nt":  # Windows
            try:
                subprocess.run(["explorer", "/select,", file_path])
            except Exception as e:
                print(f"Error opening file explorer: {e}")
        elif os.name == "posix":  # macOS and Linux
            try:
                if sys.platform == "darwin":  # macOS
                    subprocess.run(["open", "-R", file_path])
                else:  # Linux
                    subprocess.run(["xdg-open", os.path.dirname(file_path)])
            except Exception as e:
                print(f"Error opening file explorer: {e}")
    else:
        print(f"File does not exist: {file_path}")


def translate_tkinter_bind_to_hotkey(bind_str: str) -> str:
    """Translate a tkinter bind string to a hotkey string.

    Example:
        "<Control-s>" -> "Ctrl+S"
        "<Shift-Alt-A>" -> "Shift+Alt+A"
    """
    if not (bind_str.startswith("<") and bind_str.endswith(">")):
        return bind_str  # not a valid bind string
    parts = bind_str[1:-1].split("-")
    translations = {
        "Control": "Ctrl",
        "Return": "Enter",
        "Escape": "Esc",
    }
    for i, part in enumerate(parts):
        if part in translations:
            parts[i] = translations[part]
        elif len(part) == 1:
            parts[i] = part.upper()
    return "+".join(parts)


def dump_stack_trace() -> None:
    """Dump the current stack trace to the console for debugging purposes."""
    if IS_DEBUG_MODE:
        print("[DEBUG] Stack trace:")
        for frame in inspect.stack()[1:]:
            print(
                f'  File "{frame.filename}", line {frame.lineno}, in {frame.function}'
            )


def do_nothing() -> None:
    """A no-op function that does nothing."""
    if IS_DEBUG_MODE:
        # get the caller function name and stack info
        caller = inspect.stack()[1]
        print(
            f"[DEBUG] do_nothing() called from {caller.function} in {caller.filename}:{caller.lineno}"
        )
    pass

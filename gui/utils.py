import os
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


def ask_save_file_dialog(exts: list[str]) -> str | None:
    """Open a save file dialog and return the selected file path."""
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    file_path = filedialog.asksaveasfilename(
        defaultextension=exts[0], filetypes=[("Supported Files", exts)]
    )
    root.destroy()
    if len(file_path) == 0:
        return None
    if "." not in file_path and len(exts) > 0:
        file_path += exts[0]
    if file_path:
        return os.path.abspath(file_path)
    return None


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

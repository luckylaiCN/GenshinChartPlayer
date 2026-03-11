import os

import customtkinter as ctk

from tkinter import ttk
from typing import Callable

from gui.theme import curr_theme
from gui.widgets.sidebars.base import FunctionalFrame
from gui.utils import ask_open_folder_dialog

from shared.settings import MAX_DICTORY_ENTRIES, ACCEPTED_FILE_EXTENSIONS

PathType = dict[str, "PathType"] | str
FolderType = dict[str, PathType]


class FileFunctionalFrame(FunctionalFrame):
    target_path: str | None = None
    tree_view: ttk.Treeview | None = None
    open_callback: Callable[[str], None] | None = None

    def __init__(
        self,
        master=None,
        open_callback: Callable[[str], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, **kwargs)
        self.open_callback = open_callback

    def register_open_callback(self, open_callback: Callable[[str], None]) -> None:
        self.open_callback = open_callback

    def create_widgets(self):
        # Add file-related buttons or options here
        self.label = ctk.CTkLabel(
            self,
            text="Open a folder to get started.",
            text_color=curr_theme.TEXT_PRIMARY,
        )
        self.label.pack(pady=10)
        # open folder button
        self.open_folder_btn = ctk.CTkButton(
            self,
            text="Open Folder",
            command=self.open_folder_dialog,
            fg_color=curr_theme.BTN_PRIMARY,
            text_color=curr_theme.TEXT_PRIMARY,
        )

        self.open_folder_btn.pack(pady=10)

        self.update_folder_btn = ctk.CTkButton(
            self,
            text="Update Directory",
            command=self.update_directory_structure,
            fg_color=curr_theme.BTN_PRIMARY,
            text_color=curr_theme.TEXT_PRIMARY,
        )
        self.update_folder_btn.pack(pady=10)

    def open_folder_dialog(self):
        selected_path = ask_open_folder_dialog()
        if selected_path:
            self.target_path = selected_path
            self.update_directory_structure()

    def set_target_path(self, path: str) -> None:
        self.target_path = path
        self.update_directory_structure()

    def update_directory_structure(self) -> None:
        if self.target_path is None:
            return

        if not os.path.isdir(self.target_path):
            return

        dir_dict = get_dicted_dir(self.target_path)

        self.label.configure(
            text=f"Current Folder: \n{self.target_path}",
            text_color=curr_theme.TEXT_PRIMARY,
        )
        self.open_folder_btn.configure(
            text="Change Folder",
            fg_color=curr_theme.BTN_PRIMARY,
            text_color=curr_theme.TEXT_PRIMARY,
        )

        if self.tree_view is not None:
            self.tree_view.destroy()

        bg_color = self._apply_appearance_mode(curr_theme.BG_SECONDARY)
        text_color = self._apply_appearance_mode(curr_theme.TEXT_PRIMARY)

        self.ttk_style = ttk.Style()

        # configure style for empty background
        self.ttk_style.theme_use("default")

        self.ttk_style.configure(
            "Custom.Treeview",
            background=bg_color,
            fieldbackground=bg_color,
            foreground=text_color,
            rowheight=30,
        )

        # style for treeview headings
        # ttk_style.configure(
        #     "Custom.Treeview.Heading",
        #     background=bg_color,
        #     foreground=text_color,
        #     height=0,
        # )

        # config style for default font size
        default_font = self.label._font
        new_font = (default_font._family, default_font._size + 5)  # type: ignore
        self.ttk_style.configure("Custom.Treeview", font=new_font)
        self.tree_view = ttk.Treeview(
            self,
            style="Custom.Treeview",
            show="tree",  # no headings
        )
        self.tree_view.pack(fill="both", expand=True, pady=10)
        self._populate_tree_view(self.tree_view, "", dir_dict)

        # bind selection event
        self.tree_view.bind("<Double-1>", self.on_double_click)
        self.tree_view.bind("<Button-3>", self.on_right_click)

    def _populate_tree_view(
        self, tree_view: ttk.Treeview, parent: str, dir_dict: FolderType
    ) -> None:
        for name, content in dir_dict.items():
            if isinstance(content, dict):
                folder_id = tree_view.insert(parent, "end", text=name, open=False)
                self._populate_tree_view(tree_view, folder_id, content)
            else:
                tree_view.insert(parent, "end", text=name)

    def on_right_click(self, event) -> None:
        print(f"right click recv, event: {event}")
        tv = self.tree_view
        if tv is None:
            return 
        item = tv.identify_element(event.x, event.y)
        if item != "text":
            return 
        tv.selection_set(tv.identify_row(event.y))
        self._show_context_menu(event)

    def _show_context_menu(self, event) -> None:
        if self.tree_view is None:
            return
        selection = self.tree_view.selection()[0]
        if selection:
            full_path = self._get_tree_full_path(selection)
            print(f"show context menu for {full_path}")

    def on_double_click(self, event) -> None:
        if self.tree_view is None:
            return
        if self.target_path is None:
            return
        selected_item = self.tree_view.selection()[0]
        if selected_item:
            # item_text = self.tree_view.item(selected_item, "text")
            full_path = self._get_tree_full_path(selected_item)

            file_path = os.path.join(self.target_path, full_path)
            if os.path.isfile(file_path):
                self.on_select_file(file_path)

    def on_select_file(self, file_path: str) -> None:
        if self.open_callback is not None:
            self.open_callback(file_path)

    def _get_tree_full_path(self, item_id: str) -> str:
        if self.tree_view is None:
            return ""
        parts = []
        while item_id:
            item_text = self.tree_view.item(item_id, "text")
            parts.insert(0, item_text)
            item_id = self.tree_view.parent(item_id)
        return os.path.join(*parts)

    def _set_appearance_mode(self, mode: str) -> None:
        super()._set_appearance_mode(mode)
        if self.tree_view is not None:
            bg_color = self._apply_appearance_mode(curr_theme.BG_SECONDARY)
            text_color = self._apply_appearance_mode(curr_theme.TEXT_PRIMARY)
            self.ttk_style.configure(
                "Custom.Treeview",
                background=bg_color,
                fieldbackground=bg_color,
                foreground=text_color,
            )
        self.label.configure(text_color=curr_theme.TEXT_PRIMARY)
        self.open_folder_btn.configure(
            fg_color=curr_theme.BTN_PRIMARY,
            text_color=curr_theme.TEXT_PRIMARY,
        )
        self.update_folder_btn.configure(
            fg_color=curr_theme.BTN_PRIMARY,
            text_color=curr_theme.TEXT_PRIMARY,
        )


def get_base_name(path: str) -> str:
    return os.path.basename(path)


def get_dicted_dir(path: str) -> FolderType:
    dir_dict: FolderType = {}
    counter = 0
    try:
        for entry in os.listdir(path):
            full_path = os.path.join(path, entry)
            if os.path.isdir(full_path):
                result = get_dicted_dir(full_path)
                if result:  # only add non-empty directories
                    dir_dict[entry] = result
                counter += len(result)
            else:
                if any(entry.endswith(ext) for ext in ACCEPTED_FILE_EXTENSIONS):
                    dir_dict[entry] = entry
                    counter += 1
            if counter >= MAX_DICTORY_ENTRIES:
                print("Maximum directory entries reached, stopping further traversal.")
                break
    except PermissionError:
        pass  # Skip directories for which we don't have permission
    return dir_dict

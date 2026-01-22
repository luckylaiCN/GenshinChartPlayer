import customtkinter as ctk

from gui.widgets.editor import EditorFrame
from gui.widgets.sidebar import SidebarFrame
from gui.widgets.menubar import MenuBar, Menu
from gui.widgets.toast import Toast
from gui.theme import curr_theme
from gui.utils import do_nothing, ask_open_file_dialog, ask_save_file_dialog
from shared.settings import ACCEPTED_FILE_EXTENSIONS


class MainFrame(ctk.CTkFrame):
    master: ctk.CTk

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=curr_theme.BG_SECONDARY)
        self.create_menu_bar()
        self.create_widgets()

    def create_menu_bar(self):
        self.menubar = MenuBar(master=self)
        self.menubar.pack(side="top", fill="x")

        self.file_menu = Menu(master=self.menubar, menu_name="File")
        self.menubar.add_menu(self.file_menu)

        self.new_file_menu_item = Menu(
            master=self.file_menu,
            menu_name="New File",
            command=self.handle_new_file,
            hotkey="<Control-n>",
        )

        self.open_menu_item = Menu(
            master=self.file_menu,
            menu_name="Open",
            command=self.open_file_dialog,
            hotkey="<Control-o>",
        )
        self.file_menu.add_separator()
        self.save_menu_item = Menu(
            master=self.file_menu,
            menu_name="Save",
            command=self.save_current_file,
            hotkey="<Control-s>",
        )
        self.save_as_menu_item = Menu(
            master=self.file_menu,
            menu_name="Save As",
            command=self.save_current_file_as,
            hotkey="<Control-Shift-S>",
        )

        self.edit_menu = Menu(master=self.menubar, menu_name="Edit")
        self.menubar.add_menu(self.edit_menu)
        self.undo_menu_item = Menu(
            master=self.edit_menu,
            menu_name="Undo",
            command=do_nothing,
            hotkey="<Control-z>",
        )
        self.redo_menu_item = Menu(
            master=self.edit_menu,
            menu_name="Redo",
            command=do_nothing,
            hotkey="<Control-y>",
        )

    def open_file_dialog(self) -> None:
        file_path = ask_open_file_dialog(ACCEPTED_FILE_EXTENSIONS)
        if file_path is not None:
            self.editor_frame.handle_open_file(file_path)

    def create_widgets(self):
        self.sidebar_frame = SidebarFrame(
            master=self, border_width=2, border_color=curr_theme.BORDER_COLOR
        )
        self.sidebar_frame.pack(side="left", fill="y", padx=10, pady=10)

        self.editor_frame = EditorFrame(master=self)
        self.editor_frame.pack(
            side="right",
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        # register open file callback
        self.sidebar_frame.register_open_callback(self.editor_frame.handle_open_file)

    def save_current_file(self) -> None:
        curr_tab = self.editor_frame.text_areas.get_current_file_tab()
        if curr_tab is not None:
            curr_tab.update_content(self.editor_frame.text_areas.get_text_area_str())
            if curr_tab.source_path is not None:
                curr_tab.save()
                toast = Toast(
                    master=self,
                    message="File saved successfully.",
                    duration=2000,
                    position="center",
                )
                toast.show()
            else:
                # no source path, trigger save as dialog
                self.save_current_file_as()

    def save_current_file_as(self) -> None:
        curr_tab = self.editor_frame.text_areas.get_current_file_tab()
        if curr_tab is not None:
            file_path = ask_save_file_dialog(ACCEPTED_FILE_EXTENSIONS)
            if file_path is not None:
                curr_tab.update_content(
                    self.editor_frame.text_areas.get_text_area_str()
                )
                curr_tab.save(path=file_path)
                toast = Toast(
                    master=self,
                    message="File saved successfully.",
                    duration=2000,
                    position="center",
                )
                toast.show()

    def handle_new_file(self) -> None:
        self.editor_frame.handle_new_file()
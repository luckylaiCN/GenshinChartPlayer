import sys

import customtkinter as ctk

from gui.widgets.editor import EditorFrame
from gui.widgets.sidebar import SidebarFrame
from gui.widgets.sidebars.play import PlayFunctionalFrame
from gui.widgets.sidebars.file import FileFunctionalFrame
from gui.widgets.menubar import MenuBar, Menu
from gui.widgets.toast import raise_toast
from gui.widgets.notification import raise_bottom_warning
from gui.theme import curr_theme
from gui.utils import ask_open_file_dialog, ask_save_file_dialog
from shared.settings import ACCEPTED_FILE_EXTENSIONS
from shared.utils import should_request_admin_privileges, ask_for_admin_privileges
from player.handlers import imported_handler_modules


class MainFrame(ctk.CTkFrame):
    master: ctk.CTk
    topmost: bool = False

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(fg_color=curr_theme.BG_SECONDARY)
        self.create_menu_bar()
        self.create_widgets()
        self.defult_settings()

    def create_menu_bar(self):
        self.menubar = MenuBar(master=self)
        self.menubar.pack(side="top", fill="x", expand=True)

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

        self.open_new_folder_menu_item = Menu(
            master=self.file_menu,
            menu_name="Open Folder",
            command=self.handle_new_folder,
            hotkey="<Control-Shift-O>",
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

        self.file_menu.add_separator()

        self.quit_menu_item = Menu(
            master=self.file_menu,
            menu_name="Quit",
            command=self.quit_application,
            hotkey="<Control-q>",
        )

        self.edit_menu = Menu(master=self.menubar, menu_name="Edit")

        self.menubar.add_menu(self.edit_menu)

        self.format_menu_item = Menu(
            master=self.edit_menu,
            menu_name="Format Chart",
            command=self.handle_format_chart,
            hotkey="<Alt-Shift-F>",
        )

        # self.undo_menu_item = Menu(
        #     master=self.edit_menu,
        #     menu_name="Undo",
        #     command=do_nothing,
        #     hotkey="<Control-z>",
        # )
        # self.redo_menu_item = Menu(
        #     master=self.edit_menu,
        #     menu_name="Redo",
        #     command=do_nothing,
        #     hotkey="<Control-y>",
        # )
        self.settings_menu = Menu(master=self.menubar, menu_name="Settings")
        self.menubar.add_menu(self.settings_menu)
        self.toggle_topmost_menu_item = Menu(
            master=self.settings_menu,
            menu_name="Enable Always on Top",
            command=self.toggle_topmost,
        )
        self.settings_menu.add_separator()
        self.handler_selection_menu_item = Menu(
            master=self.settings_menu,
            menu_name="Player Handler",
        )
        self.handler_items = {}
        for handler_name, module in imported_handler_modules.items():
            handler_menu_item = Menu(
                master=self.handler_selection_menu_item,
                menu_name=module.name(),
                command=lambda name=handler_name: self.set_handler(name),
            )
            self.handler_items[handler_name] = handler_menu_item

        self.settings_menu.add_separator()

        self.apperence_mode_menu = Menu(
            master=self.settings_menu,
            menu_name="Appearance Mode",
        )

        app_mods = [
            ("Light Mode", "light"),
            ("Dark Mode", "dark"),
            ("System Mode", "system"),
        ]
        self.mode_menu_items = {}
        for mod_name, mod_key in app_mods:
            mod_menu_item = Menu(
                master=self.apperence_mode_menu,
                menu_name=mod_name,
                command=lambda mode=mod_key: self.toggle_appearance_mode(mode),
            )
            self.mode_menu_items[mod_key] = mod_menu_item

        self.player_menu = Menu(master=self.menubar, menu_name="Play")
        self.menubar.add_menu(self.player_menu)
        self.play_menu_item = Menu(
            master=self.player_menu,
            menu_name="Play",
            command=self.player_handle_play,
            hotkey="<F5>",
            is_super_command=True,
        )
        self.play_from_start_menu_item = Menu(
            master=self.player_menu,
            menu_name="Play from Start",
            command=self.player_handle_play_from_start,
            hotkey="<Shift-F5>",
            is_super_command=True,
        )
        self.stop_menu_item = Menu(
            master=self.player_menu,
            menu_name="Stop",
            command=self.player_handle_stop,
            hotkey="<F6>",
            is_super_command=True,
        )
        self.reset_menu_item = Menu(
            master=self.player_menu,
            menu_name="Stop and Reset",
            command=self.player_handle_stop_and_reset,
            hotkey="<F7>",
            is_super_command=True,
        )

        self.player_menu.add_separator()

        self.practice_menu_item = Menu(
            master=self.player_menu,
            menu_name="Practice Mode",
            command=self.player_handle_practice,
            hotkey="<F8>",
            is_super_command=True,
        )
        self.practice_mode_reset_menu_item = Menu(
            master=self.player_menu,
            menu_name="Practice Mode (Reset)",
            command=lambda: self.player_handle_practice(reset=True),
            hotkey="<Shift-F8>",
            is_super_command=True,
        )

        self.player_menu.add_separator()

        self.enable_floating_display_menu_item = Menu(
            master=self.player_menu,
            menu_name="Toggle Floating Display",
            command=self.toggle_floating_display,
        )

        if should_request_admin_privileges():
            self.reopen_as_admin_menu_item = Menu(
                master=self.settings_menu,
                menu_name="Reopen as Administrator",
                command=self.handle_reopen_asministrator,
            )

    def set_handler(self, handler_name: str, silent=False) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.set_handler(handler_name)
            if not silent:
                raise_toast(
                    master=self,
                    message="Player handler changed successfully.",
                    duration=2000,
                    position="center",
                )

    def toggle_topmost(self) -> None:
        self.topmost = not self.topmost
        if self.topmost:
            self.toggle_topmost_menu_item.rename("Disable Always on Top")
        else:
            self.toggle_topmost_menu_item.rename("Enable Always on Top")
        self.master.wm_attributes("-topmost", self.topmost)

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

        self.sidebar_frame.register_open_callback(self.editor_frame.handle_open_file)
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.bind_editor(self.editor_frame)
            self.editor_frame.register_callback(lambda _: play_frame.on_tab_switched())

    def save_current_file(self) -> None:
        curr_tab = self.editor_frame.text_areas.get_current_file_tab()
        if curr_tab is not None:
            curr_tab.update_content(self.editor_frame.text_areas.get_text_area_str())
            if curr_tab.source_path is not None:
                curr_tab.save()
                raise_toast(
                    master=self,
                    message="File saved successfully.",
                    duration=2000,
                    position="center",
                )
            else:
                # no source path, trigger save as dialog
                self.save_current_file_as()

    def save_current_file_as(self) -> None:
        curr_tab = self.editor_frame.text_areas.get_current_file_tab()
        if curr_tab is not None:
            old_name = curr_tab.tab_identifier
            old_path = curr_tab.source_path
            file_path = ask_save_file_dialog(ACCEPTED_FILE_EXTENSIONS)
            if file_path is not None:
                curr_tab.update_content(
                    self.editor_frame.text_areas.get_text_area_str()
                )
                curr_tab.save(path=file_path)
                raise_toast(
                    master=self,
                    message="File saved successfully.",
                    duration=2000,
                    position="center",
                )
                new_name = curr_tab.tab_identifier
                new_path = curr_tab.source_path
                self.editor_frame.rename_tab(old_name, new_name)
                self.editor_frame.remove_path_from_opened(old_path)
                self.editor_frame.add_path_to_opened(new_path)

    def handle_new_file(self) -> None:
        self.editor_frame.handle_new_file()

    def handle_new_folder(self) -> None:
        file_fun = self.sidebar_frame.get_functional_frame("Files")
        if isinstance(file_fun, FileFunctionalFrame):
            file_fun.open_folder_dialog()

    def toggle_appearance_mode(self, mode: str) -> None:
        ctk.set_appearance_mode(mode)

    def defult_settings(self) -> None:
        default_handler = "player.handlers.sound_h"
        if default_handler in imported_handler_modules.keys():
            self.set_handler(default_handler, silent=True)

        if should_request_admin_privileges():
            raise_bottom_warning(
                master=self,
                text="Some features may require administrator privileges. "
                "You can reopen the application as administrator from the Settings menu.",
            )

    def player_handle_play(self) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.request_play()

    def player_handle_stop(self) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.request_stop()

    def player_handle_stop_and_reset(self) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.request_stop_and_reset()

    def player_handle_play_from_start(self) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.request_play_from_start()

    def handle_reopen_asministrator(self) -> None:
        if should_request_admin_privileges():
            ask_for_admin_privileges()
            sys.exit(0)

    def toggle_floating_display(self) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.toggle_floating_display()

    def player_handle_practice(self, reset=False) -> None:
        play_frame = self.sidebar_frame.get_functional_frame("Player")
        if isinstance(play_frame, PlayFunctionalFrame):
            play_frame.toggle_practice_mode(reset=reset)

    def quit_application(self) -> None:
        self.master.quit()

    def handle_format_chart(self) -> None:
        self.editor_frame.format_chart()

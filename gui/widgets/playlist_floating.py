import os
import customtkinter as ctk

from gui.theme import curr_theme
from shared.settings import ACCEPTED_FILE_EXTENSIONS
from gui.utils import ask_open_file_dialog
from player.playlist import PlayMode

PLAY_CHAR = "▶"
PAUSE_CHAR = "⏸"
STOP_CHAR = "■"
NEXT_CHAR = "⏭"
PREV_CHAR = "⏮"


class PlaylistFloatingWindow(ctk.CTkToplevel):
    def __init__(self, play_frame=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.play_frame = play_frame
        self.title("Playlist")
        self.geometry("360x480")
        self.minsize(280, 300)

        self._entry_widgets: list[ctk.CTkButton] = []
        self._cached_state_key: tuple = ()
        self.protocol("WM_DELETE_WINDOW", self._close)

        self._create_widgets()
        self._sync_from_playlist()

    def _state_key(self) -> tuple:
        if self.play_frame is None:
            return ()
        pl = self.play_frame.playlist
        return (
            len(pl.entries),
            pl.current_index,
            self.play_frame.playlist_selected_index,
            self.play_frame._playlist_playing,
            pl.play_mode.value,
        )

    def _create_widgets(self):
        self.configure(fg_color=curr_theme.BG_SECONDARY)

        header = ctk.CTkFrame(self, fg_color=curr_theme.BG_PRIMARY, height=32)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="Playlist", text_color=curr_theme.TEXT_PRIMARY,
            font=ctk.CTkFont(size=14, weight="bold"),
        ).pack(side="left", padx=10, pady=4)

        self.pl_current_label = ctk.CTkLabel(
            header, text="", text_color=curr_theme.TEXT_SECONDARY,
            font=ctk.CTkFont(size=11),
        )
        self.pl_current_label.pack(side="left", padx=10, pady=4)

        self.pl_list_frame = ctk.CTkScrollableFrame(
            self, fg_color=curr_theme.BG_PRIMARY,
        )
        self.pl_list_frame.pack(fill="both", expand=True, padx=5, pady=2)

        mode_frame = ctk.CTkFrame(self, fg_color=curr_theme.BG_SECONDARY)
        mode_frame.pack(fill="x", padx=5, pady=1)
        self.mode_var = ctk.StringVar(value=PlayMode.SEQUENTIAL_LOOP.value)
        for mode, label in [
            (PlayMode.SEQUENTIAL_LOOP, "Seq"),
            (PlayMode.SINGLE_LOOP, "Single"),
            (PlayMode.SHUFFLE, "Shuffle"),
        ]:
            rb = ctk.CTkRadioButton(
                mode_frame, text=label, variable=self.mode_var,
                value=mode.value, command=self._on_mode_change,
                text_color=curr_theme.TEXT_PRIMARY,
            )
            rb.pack(side="left", padx=4, pady=2, expand=True)

        transport = ctk.CTkFrame(self, fg_color=curr_theme.BG_SECONDARY)
        transport.pack(fill="x", padx=5, pady=1)
        self.pl_play_btn = ctk.CTkButton(
            transport, text=PLAY_CHAR, command=self._on_play_pause,
            fg_color=curr_theme.BTN_PRIMARY, width=40, font=("Consolas", 14),
        )
        self.pl_play_btn.pack(side="left", padx=2, pady=2, expand=True, fill="x")
        ctk.CTkButton(
            transport, text=PREV_CHAR, command=self._on_prev,
            fg_color=curr_theme.BTN_PRIMARY, width=40, font=("Consolas", 14),
        ).pack(side="left", padx=2, pady=2, expand=True, fill="x")
        ctk.CTkButton(
            transport, text=STOP_CHAR, command=self._on_stop,
            fg_color=curr_theme.ERROR_COLOR, width=40, font=("Consolas", 14),
        ).pack(side="left", padx=2, pady=2, expand=True, fill="x")
        ctk.CTkButton(
            transport, text=NEXT_CHAR, command=self._on_next,
            fg_color=curr_theme.BTN_PRIMARY, width=40, font=("Consolas", 14),
        ).pack(side="left", padx=2, pady=2, expand=True, fill="x")

        action1 = ctk.CTkFrame(self, fg_color=curr_theme.BG_SECONDARY)
        action1.pack(fill="x", padx=5, pady=1)
        ctk.CTkButton(
            action1, text="File\u2026", command=self._on_add,
            fg_color=curr_theme.BTN_PRIMARY, height=28,
        ).pack(side="left", padx=1, pady=1, expand=True, fill="x")
        ctk.CTkButton(
            action1, text="Editor", command=self._on_add_current,
            fg_color=curr_theme.BTN_PRIMARY, height=28,
        ).pack(side="left", padx=1, pady=1, expand=True, fill="x")
        self.pl_remove_btn = ctk.CTkButton(
            action1, text="Remove", command=self._on_remove,
            fg_color=curr_theme.BTN_PRIMARY, height=28,
        )
        self.pl_remove_btn.pack(side="left", padx=1, pady=1, expand=True, fill="x")
        self.pl_clear_btn = ctk.CTkButton(
            action1, text="Clear", command=self._on_clear,
            fg_color=curr_theme.BTN_PRIMARY, height=28,
        )
        self.pl_clear_btn.pack(side="left", padx=1, pady=1, expand=True, fill="x")

        action2 = ctk.CTkFrame(self, fg_color=curr_theme.BG_SECONDARY)
        action2.pack(fill="x", padx=5, pady=(1, 5))
        self.pl_up_btn = ctk.CTkButton(
            action2, text="\u2191", command=self._on_move_up,
            fg_color=curr_theme.BTN_PRIMARY, width=40,
        )
        self.pl_up_btn.pack(side="left", padx=2, pady=1, expand=True, fill="x")
        self.pl_down_btn = ctk.CTkButton(
            action2, text="\u2193", command=self._on_move_down,
            fg_color=curr_theme.BTN_PRIMARY, width=40,
        )
        self.pl_down_btn.pack(side="left", padx=2, pady=1, expand=True, fill="x")

        self._sync_timer()

    def _sync_from_playlist(self) -> None:
        if self.play_frame is None:
            return
        new_key = self._state_key()
        if new_key != self._cached_state_key:
            self._cached_state_key = new_key
            self._rebuild_list()
        self._update_controls_state()
        self.update_play_button()
        self.mode_var.set(self.play_frame.playlist.play_mode.value)

    def _sync_timer(self) -> None:
        if not self.winfo_exists():
            return
        self._sync_from_playlist()
        self.after(500, self._sync_timer)

    def request_rebuild(self) -> None:
        self._cached_state_key = ()
        self._sync_from_playlist()

    # --- delegated actions ---

    def _on_mode_change(self) -> None:
        if self.play_frame is None:
            return
        try:
            self.play_frame.playlist.play_mode = PlayMode(self.mode_var.get())
        except ValueError:
            pass

    def _on_add(self) -> None:
        if self.play_frame is None:
            return
        paths = ask_open_file_dialog(ACCEPTED_FILE_EXTENSIONS, multiple=True)
        if paths is None:
            return
        if isinstance(paths, str):
            paths = [paths]
        for fp in paths:
            if os.path.isfile(fp):
                self.play_frame.playlist.add_entry(fp)
        self.request_rebuild()

    def _on_add_current(self) -> None:
        if self.play_frame is None:
            return
        self.play_frame._pl_on_add_current()
        self.request_rebuild()

    def _on_remove(self) -> None:
        if self.play_frame is None:
            return
        self.play_frame._pl_on_remove()
        self.request_rebuild()

    def _on_clear(self) -> None:
        if self.play_frame is None:
            return
        self.play_frame._pl_on_clear()
        self.request_rebuild()

    def _on_move_up(self) -> None:
        if self.play_frame is None:
            return
        self.play_frame._pl_on_move_up()
        self.request_rebuild()

    def _on_move_down(self) -> None:
        if self.play_frame is None:
            return
        self.play_frame._pl_on_move_down()
        self.request_rebuild()

    def _on_play_pause(self) -> None:
        if self.play_frame is None:
            return
        self.play_frame._pl_on_play_pause()

    def _on_next(self) -> None:
        if self.play_frame is None:
            return
        self.play_frame._pl_on_next()

    def _on_prev(self) -> None:
        if self.play_frame is None:
            return
        self.play_frame._pl_on_prev()

    def _on_stop(self) -> None:
        if self.play_frame is None:
            return
        self.play_frame._pl_on_stop()

    def _rebuild_list(self) -> None:
        if self.play_frame is None:
            return
        for w in self._entry_widgets:
            w.destroy()
        self._entry_widgets.clear()

        playlist = self.play_frame.playlist
        for i, entry in enumerate(playlist.entries):
            is_current = i == playlist.current_index and self.play_frame._playlist_playing
            is_selected = i == self.play_frame.playlist_selected_index
            prefix = "\u25b6 " if is_current else "  "
            btn = ctk.CTkButton(
                self.pl_list_frame,
                text=f"{prefix}{entry.title}",
                anchor="w",
                fg_color=curr_theme.PLAYING_HIGHLIGHT_BG if is_current else (
                    curr_theme.HIGHLIGHT_COLOR if is_selected else curr_theme.BG_PRIMARY
                ),
                text_color=curr_theme.TEXT_PRIMARY,
                hover_color=curr_theme.BG_HOVER,
                command=lambda idx=i: self._select_entry(idx),
                height=26,
            )
            btn.pack(fill="x", padx=2, pady=1)
            self._entry_widgets.append(btn)

        entry = playlist.current_entry
        if entry and self.play_frame._playlist_playing:
            self.pl_current_label.configure(text=f"Now: {entry.title}")
        else:
            self.pl_current_label.configure(text="")

    def _select_entry(self, index: int) -> None:
        if self.play_frame is None:
            return
        self.play_frame.playlist_selected_index = index
        self.request_rebuild()

    def _update_controls_state(self) -> None:
        if self.play_frame is None:
            return
        playlist = self.play_frame.playlist
        has = not playlist.is_empty
        sel = 0 <= self.play_frame.playlist_selected_index < len(playlist.entries)
        self.pl_remove_btn.configure(state="normal" if sel else "disabled")
        self.pl_up_btn.configure(state="normal" if sel and self.play_frame.playlist_selected_index > 0 else "disabled")
        self.pl_down_btn.configure(state="normal" if sel and self.play_frame.playlist_selected_index < len(playlist.entries) - 1 else "disabled")
        self.pl_play_btn.configure(state="normal" if has else "disabled")
        self.pl_clear_btn.configure(state="normal" if has else "disabled")

    def update_play_button(self) -> None:
        if self.play_frame is None:
            return
        if self.play_frame._playlist_playing:
            self.pl_play_btn.configure(text=PAUSE_CHAR)
        else:
            self.pl_play_btn.configure(text=PLAY_CHAR)

    def _close(self) -> None:
        self.withdraw()

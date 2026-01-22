import time
import threading

import customtkinter as ctk

from gui.theme import curr_theme
from gui.widgets.sidebars.base import FunctionalFrame
from gui.widgets.editor import EditorFrame
from gui.widgets.toast import raise_toast
from shared.utils import global_operation_lock, OperationLockState
from player.runtime import PlayerThreadingPool
from player.handlers import imported_handler_modules

PLAY_CHARACTER = "▶"
PAUSE_CHARACTER = "⏯"
PLAY_STARTOVER_CHARACTER = "⟲"
STOP_CHARACTER = "■"


class PlayFunctionalFrame(FunctionalFrame):
    binded_editor: EditorFrame | None = None
    is_playing: bool = False
    handler_name: str = ""
    ptp: PlayerThreadingPool | None = None
    begin_time: float = 0.0

    def bind_editor(self, editor: EditorFrame) -> None:
        self.binded_editor = editor

    def set_handler(self, handler_name: str) -> None:
        self.handler_name = handler_name
        self.handler_label.configure(text=f"Handler: {self.handler_string}")

    @property
    def handler_string(self) -> str:
        handler = imported_handler_modules.get(self.handler_name, None)
        if handler is None:
            return "No Handler"
        return handler.name()

    def create_widgets(self):
        # button group
        self.button_group = ctk.CTkFrame(self, fg_color=curr_theme.BG_SECONDARY)
        # text label
        self.label = ctk.CTkLabel(
            self.button_group,
            text="Playing Controls",
            text_color=curr_theme.TEXT_PRIMARY,
        )
        # handler label
        self.handler_label = ctk.CTkLabel(
            self.button_group,
            text=f"Handler: {self.handler_string}",
            text_color=curr_theme.TEXT_SECONDARY,
        )
        # play - pause button
        self.play_pause_button = ctk.CTkButton(
            self.button_group,
            text=PLAY_CHARACTER,
            fg_color=curr_theme.BTN_PRIMARY,
            command=self.handle_play_pause,
            width=50,
            font=("Consolas", 14),
        )
        # playover - stop button
        self.playover_stop_button = ctk.CTkButton(
            self.button_group,
            text=PLAY_STARTOVER_CHARACTER,
            fg_color=curr_theme.BTN_PRIMARY,
            command=self.handle_playover_stop,
            width=50,
            font=("Consolas", 14),
        )
        # pack buttons in the center

        self.label.pack(pady=10)
        self.handler_label.pack(pady=5)
        self.play_pause_button.pack(side="left", padx=10, pady=10)
        self.playover_stop_button.pack(side="right", padx=10, pady=10)
        self.button_group.pack(pady=20)

    def _check_before_playing(self) -> bool:
        if self.binded_editor is None:
            return False
        if self.binded_editor.text_areas.curr_text_area is None:
            raise_toast(
                master=self,
                message="Open or create a new chart to get started.",
                duration=3000,
                position="center",
            )
            return False
        if self.binded_editor.runtime is None:
            raise_toast(
                master=self,
                message="No chart loaded in the editor. Please check error messages.",
                duration=3000,
                position="center",
            )
            return False
        return True

    def _play(self, reset=False) -> bool:
        if not self._check_before_playing():
            return False
        if self.binded_editor is None or self.binded_editor.runtime is None:
            return False

        runtime = self.binded_editor.runtime
        handler_module = imported_handler_modules.get(self.handler_name, None)
        if handler_module is None:
            raise_toast(
                master=self,
                message="Select a valid handler in the settings menubar before playing.",
                duration=3000,
                position="center",
            )
            return False
        self.is_playing = True
        self.play_pause_button.configure(text=PAUSE_CHARACTER)
        global_operation_lock.set_state(OperationLockState.PLAYING)
        self.ptp = PlayerThreadingPool(
            beats=runtime.get_playlist(),
            handler=handler_module.handler,
        )
        beat = 0 if reset else self.binded_editor._curr_beat_index
        if beat < 0 or beat >= len(self.ptp.beats):
            beat = 0

        self.ptp.set_beat_index(beat)
        self.binded_editor.set_current_beat_index(beat)

        threading.Thread(target=self.ptp.play_loop).start()

        self.begin_time = self.ptp.play()
        self.binded_editor.modify_editable(False)

        self.after(100, self._update_editor_current_beat)

        return True

    def _update_editor_current_beat(self):
        if self.binded_editor is None or self.ptp is None:
            return
        if self.ptp.stop_flag.get():
            if self.is_playing:
                self._stop()
            return
        editor_index = self.binded_editor._curr_beat_index
        desired_index = editor_index
        runtime = self.binded_editor.runtime
        if runtime is None:
            return
        while (
            runtime.playlist[desired_index].begin_time + self.begin_time < time.time()
        ):
            desired_index += 1
            if desired_index >= len(runtime.playlist):
                break
        if desired_index != editor_index:
            self.binded_editor.set_current_beat_index(desired_index - 1)
        if desired_index < len(runtime.playlist):
            self.after(100, self._update_editor_current_beat)
        else:
            self.after(
                1000, self._stop
            )  # wait a bit before stopping. otherwise last note may be cut off.

    def _stop(self, reset=False):
        if self.ptp is not None:
            self.ptp.stop()
        if reset and self.binded_editor is not None:
            self.binded_editor.set_current_beat_index(0)
        if self.binded_editor is not None:
            self.binded_editor.modify_editable(True)
        self.is_playing = False
        self.play_pause_button.configure(text=PLAY_CHARACTER)
        global_operation_lock.release()

    def handle_play_pause(self):
        if not self._check_before_playing():
            return
        if self.is_playing:
            self._stop()

        else:
            if global_operation_lock.is_free():
                self._play()

            else:
                # cannot play, already locked
                raise_toast(
                    master=self,
                    message="Cannot start playing: another operation is in progress.",
                    duration=3000,
                    position="center",
                )
                return

    def handle_playover_stop(self):
        if not self._check_before_playing():
            return
        if self.is_playing:
            self._stop(reset=True)
        else:
            if global_operation_lock.is_free():
                self._play(reset=True)
            else:
                raise_toast(
                    master=self,
                    message="Cannot start playing: another operation is in progress.",
                    duration=3000,
                    position="center",
                )
                return

    def request_play(self) -> bool:
        if not self._check_before_playing():
            return False
        if global_operation_lock.is_free():
            self._play()
            return True
        else:
            raise_toast(
                master=self,
                message="Cannot start playing: another operation is in progress.",
                duration=3000,
                position="center",
            )
            return False

    def request_stop(self) -> bool:
        if self.is_playing:
            self._stop()

            return True
        else:
            raise_toast(
                master=self,
                message="Playing is not currently active.",
                duration=2000,
                position="center",
            )
            return False

    def request_play_from_start(self) -> bool:
        if not self._check_before_playing():
            return False
        if global_operation_lock.is_free():
            return self._play(reset=True)
        else:
            raise_toast(
                master=self,
                message="Cannot start playing: another operation is in progress.",
                duration=3000,
                position="center",
            )
            return False

    def request_stop_and_reset(self) -> bool:
        if self.is_playing:
            self._stop(reset=True)

            return True
        else:
            raise_toast(
                master=self,
                message="Playing is not currently active.",
                duration=2000,
                position="center",
            )
            return False

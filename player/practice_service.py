import threading

from player.practice import PracticeController


class PracticeService:
    controller: PracticeController | None

    def __init__(self) -> None:
        self.controller = None

    def start(
        self,
        beat_containers: list,
        begin_beat_index: int,
        on_update_index,
        on_stop,
    ) -> bool:
        if self.is_running():
            return False
        self.controller = PracticeController(
            beat_containers=beat_containers,
            on_update_index=on_update_index,
            on_stop=on_stop,
        )
        threading.Thread(target=self.controller.start, args=(begin_beat_index,)).start()
        return True

    def stop(self) -> None:
        if self.controller is not None:
            self.controller.stop()

    def is_running(self) -> bool:
        return self.controller is not None and not self.controller.should_stop.get()
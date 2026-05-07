from player.handlers import HandlerProtocol
from player.runtime import ChartRuntime, PlayerThreadingPool


class PlaybackService:
    ptp: PlayerThreadingPool | None
    begin_time: float

    def __init__(self) -> None:
        self.ptp = None
        self.begin_time = 0.0

    def start(
        self,
        runtime: ChartRuntime,
        handler_module: HandlerProtocol,
        speed_multiplier: float,
        beat_index: int = 0,
    ) -> float:
        if self.is_running():
            return self.begin_time
        runtime.internal_property.set_speed_multiplier(speed_multiplier)
        runtime.caculate_playlist()

        self.ptp = PlayerThreadingPool(
            beats=runtime.get_playlist(), handler=handler_module.handler,
            speed_multiplier=speed_multiplier,
        )
        self.set_beat_index(beat_index)
        self.begin_time = self.ptp.play()
        return self.begin_time

    def stop(self) -> None:
        if self.ptp is not None:
            self.ptp.stop()

    def set_beat_index(self, index: int) -> None:
        if self.ptp is None:
            return
        self.ptp.set_beat_index(index)

    def is_running(self) -> bool:
        return self.ptp is not None and not self.ptp.stop_flag.get()

    def has_pool(self) -> bool:
        return self.ptp is not None

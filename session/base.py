from typing import Protocol, Any


class RecoverableWidget(Protocol):
    def dump_session(self) -> Any: ...

    def load_session(self, data: Any) -> None: ...


class ConfigurationItem(Protocol):
    def dump_configuration(self) -> Any: ...

    def load_configuration(self, data: Any) -> None: ...


VERSION = 0

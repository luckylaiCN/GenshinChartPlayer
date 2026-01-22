import importlib

from typing import Protocol
from player.pattern import NoteContainer
from player.utils import FlagBoolean


class HandlerProtocol(Protocol):
    def handler(
        self, note_container: NoteContainer, cancel_flag: FlagBoolean, begin_time: float
    ) -> None: ...

    def available(self) -> bool: ...

    def name(self) -> str: ...


# Dynamically import all handler modules in the current package
handler_modules = [
    "player.handlers.sound_h",
    "player.handlers.keyboard_h",
]


def import_safe(module_name: str) -> HandlerProtocol | None:
    try:
        module = importlib.import_module(module_name)  # type: ignore
        # Verify that the module conforms to HandlerProtocol
        if (
            hasattr(module, "handler")
            and hasattr(module, "available")
            and hasattr(module, "name")
        ):
            available_func = getattr(module, "available")
            if not callable(available_func) or not available_func():
                return None
            name_func = getattr(module, "name")
            if not callable(name_func):
                return None
            name = name_func()
            if not isinstance(name, str):
                return None
            handler_func = getattr(module, "handler")
            if not callable(handler_func):
                return None
            # note: type checker cannot verify dynamically imported modules.
            # We only check for the existence of required attributes here.
            # The caller should ensure the correctness of the module.
            return module  # type: ignore
        else:
            return None
    except ImportError:
        return None


imported_handler_modules: dict[str, HandlerProtocol] = {}

for module_name in handler_modules:
    module = import_safe(module_name)
    if module is not None:
        imported_handler_modules[module_name] = module

__all__ = ["imported_handler_modules", "HandlerProtocol"]

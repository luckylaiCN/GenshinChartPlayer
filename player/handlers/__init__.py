import importlib

from typing import ItemsView, Protocol
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
    "player.handlers.donothing_h",
    "player.handlers.keyboard_h",
    "player.handlers.keyboard_longpress_h",
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

fallback_handler_module_name = "player.handlers.donothing_h"
if fallback_handler_module_name not in imported_handler_modules:
    fallback_candidate = import_safe(fallback_handler_module_name)
    if fallback_candidate is not None:
        imported_handler_modules[fallback_handler_module_name] = fallback_candidate
    else:
        raise ImportError(
            f"Failed to import fallback handler module '{fallback_handler_module_name}'. No valid handlers available."
        )
    
fallback_module: HandlerProtocol = imported_handler_modules[fallback_handler_module_name]

def iter_handler_modules() -> ItemsView[str, HandlerProtocol]:
    return imported_handler_modules.items()


def get_handler_module(handler_name: str) -> HandlerProtocol | None:
    return imported_handler_modules.get(handler_name)


def get_fallback_handler_module() -> HandlerProtocol:
    return fallback_module


__all__ = [
    "imported_handler_modules",
    "HandlerProtocol",
    "fallback_module",
    "iter_handler_modules",
    "get_handler_module",
    "get_fallback_handler_module",
]

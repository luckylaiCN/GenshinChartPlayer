from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Callable, Any

try:
    from AppKit import (
        NSEvent,
        NSEventMaskKeyDown,
        NSEventMaskKeyUp,
        NSEventModifierFlagCommand,
        NSEventModifierFlagControl,
        NSEventModifierFlagOption,
        NSEventModifierFlagShift,
    )
    from Quartz import CGEventCreateKeyboardEvent, CGEventPost, kCGHIDEventTap
except Exception:
    NSEvent = None
    NSEventMaskKeyDown = None
    NSEventMaskKeyUp = None
    NSEventModifierFlagCommand = None
    NSEventModifierFlagControl = None
    NSEventModifierFlagOption = None
    NSEventModifierFlagShift = None
    CGEventCreateKeyboardEvent = None
    CGEventPost = None
    kCGHIDEventTap = None


_MAC_KEY_CODES: dict[str, int] = {
    "a": 0,
    "s": 1,
    "d": 2,
    "f": 3,
    "h": 4,
    "g": 5,
    "z": 6,
    "x": 7,
    "c": 8,
    "v": 9,
    "b": 11,
    "q": 12,
    "w": 13,
    "e": 14,
    "r": 15,
    "y": 16,
    "t": 17,
    "u": 32,
    "i": 34,
    "o": 31,
    "p": 35,
    "j": 38,
    "k": 40,
    "l": 37,
    "m": 46,
    "n": 45,
    "f1": 122,
    "f2": 120,
    "f3": 99,
    "f4": 118,
    "f5": 96,
    "f6": 97,
    "f7": 98,
    "f8": 100,
    "f9": 101,
    "f10": 109,
    "f11": 103,
    "f12": 111,
    "enter": 36,
    "return": 36,
    "escape": 53,
    "esc": 53,
    "tab": 48,
    "space": 49,
}

_MODIFIER_TOKEN_TO_FLAG = {
    "ctrl": NSEventModifierFlagControl,
    "shift": NSEventModifierFlagShift,
    "alt": NSEventModifierFlagOption,
    "option": NSEventModifierFlagOption,
    "command": NSEventModifierFlagCommand,
    "cmd": NSEventModifierFlagCommand,
    "meta": NSEventModifierFlagCommand,
}

_KEY_CODE_TO_TOKEN = {code: token for token, code in _MAC_KEY_CODES.items()}


def native_keyboard_backend_available() -> bool:
    return (
        sys.platform == "darwin"
        and NSEvent is not None
        and CGEventCreateKeyboardEvent is not None
        and CGEventPost is not None
        and kCGHIDEventTap is not None
    )


def _normalize_hotkey(bind_str: str) -> tuple[frozenset[str], str]:
    if not (bind_str.startswith("<") and bind_str.endswith(">")):
        return frozenset(), bind_str.lower()

    modifiers: set[str] = set()
    key_token = ""
    for part in bind_str[1:-1].split("-"):
        normalized = part.lower()
        if normalized in ("control", "ctrl"):
            modifiers.add("ctrl")
        elif normalized == "shift":
            modifiers.add("shift")
        elif normalized in ("alt", "option"):
            modifiers.add("alt")
        elif normalized in ("command", "cmd", "meta"):
            modifiers.add("command")
        else:
            key_token = normalized
    return frozenset(modifiers), key_token


def _event_modifiers(event: Any) -> frozenset[str]:
    flags = int(event.modifierFlags())
    modifiers: set[str] = set()
    if NSEventModifierFlagControl is not None and flags & NSEventModifierFlagControl:
        modifiers.add("ctrl")
    if NSEventModifierFlagShift is not None and flags & NSEventModifierFlagShift:
        modifiers.add("shift")
    if NSEventModifierFlagOption is not None and flags & NSEventModifierFlagOption:
        modifiers.add("alt")
    if NSEventModifierFlagCommand is not None and flags & NSEventModifierFlagCommand:
        modifiers.add("command")
    return frozenset(modifiers)


def _event_key_token(event: Any) -> str:
    key_code = int(event.keyCode())
    token = _KEY_CODE_TO_TOKEN.get(key_code)
    if token is not None:
        return token

    characters = event.charactersIgnoringModifiers()
    if characters:
        return str(characters).lower()
    return ""


@dataclass
class NativeMonitorHandle:
    handles: list[Any]

    def stop(self) -> None:
        if not native_keyboard_backend_available():
            self.handles.clear()
            return
        for handle in self.handles:
            try:
                NSEvent.removeMonitor_(handle)
            except Exception:
                pass
        self.handles.clear()


def register_hotkey(
    bind_str: str, callback: Callable[[], object | None]
) -> NativeMonitorHandle | None:
    if not native_keyboard_backend_available():
        return None

    required_modifiers, required_key = _normalize_hotkey(bind_str)

    def handle_event(event: Any):
        if getattr(event, "isARepeat", lambda: False)():
            return event
        if _event_key_token(event) != required_key:
            return event
        if _event_modifiers(event) != required_modifiers:
            return event
        callback()
        return event

    monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
        NSEventMaskKeyDown, handle_event
    )
    return NativeMonitorHandle([monitor])


def register_key_listeners(
    keys: list[str],
    on_press: Callable[[str], None],
    on_release: Callable[[str], None],
) -> NativeMonitorHandle | None:
    if not native_keyboard_backend_available():
        return None

    normalized_keys = {key.lower(): key for key in keys}

    def handle_press(event: Any):
        key_token = _event_key_token(event)
        if key_token in normalized_keys:
            on_press(normalized_keys[key_token])
        return event

    def handle_release(event: Any):
        key_token = _event_key_token(event)
        if key_token in normalized_keys:
            on_release(normalized_keys[key_token])
        return event

    press_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
        NSEventMaskKeyDown, handle_press
    )
    release_monitor = NSEvent.addLocalMonitorForEventsMatchingMask_handler_(
        NSEventMaskKeyUp, handle_release
    )
    return NativeMonitorHandle([press_monitor, release_monitor])


def press_and_release(key_name: str) -> None:
    if not native_keyboard_backend_available():
        raise RuntimeError("Native macOS keyboard backend is unavailable.")

    key_code = _MAC_KEY_CODES.get(key_name.lower())
    if key_code is None:
        raise ValueError(f"Unsupported macOS key: {key_name}")

    down_event = CGEventCreateKeyboardEvent(None, key_code, True)
    up_event = CGEventCreateKeyboardEvent(None, key_code, False)
    CGEventPost(kCGHIDEventTap, down_event)
    CGEventPost(kCGHIDEventTap, up_event)

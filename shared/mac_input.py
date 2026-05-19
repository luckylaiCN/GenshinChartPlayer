from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass
from typing import Callable, Protocol, Sequence, cast

from shared.utils import dispatch_to_main_thread





class _KeyboardEvent(Protocol):
    def modifierFlags(self) -> int: ...

    def keyCode(self) -> int: ...

    def charactersIgnoringModifiers(self) -> str | None: ...

    def isARepeat(self) -> bool: ...


class _NSEventClass(Protocol):
    @staticmethod
    def addGlobalMonitorForEventsMatchingMask_handler_(
        mask: int, handler: Callable[[_KeyboardEvent], None]
    ) -> object: ...

    @staticmethod
    def removeMonitor_(monitor: object) -> None: ...


class _AppKitModule(Protocol):
    NSEvent: _NSEventClass
    NSEventMaskKeyDown: int
    NSEventMaskKeyUp: int
    NSEventModifierFlagCommand: int
    NSEventModifierFlagControl: int
    NSEventModifierFlagOption: int
    NSEventModifierFlagShift: int


class _QuartzModule(Protocol):
    CGPreflightListenEventAccess: Callable[[], bool]
    CGRequestListenEventAccess: Callable[[], bool]
    CGEventCreateKeyboardEvent: Callable[[object | None, int, bool], object]
    CGEventPost: Callable[[int, object], None]
    kCGHIDEventTap: int


class _ApplicationServicesModule(Protocol):
    AXIsProcessTrustedWithOptions: Callable[[object], bool]
    kAXTrustedCheckOptionPrompt: object

try:
    import AppKit as _AppKit
    import ApplicationServices as _ApplicationServices
    import Quartz as _Quartz
except Exception:
    _AppKit = None
    _ApplicationServices = None
    _Quartz = None

if _AppKit is not None:
    appkit = cast(_AppKitModule, _AppKit)
    NSEvent: _NSEventClass | None = appkit.NSEvent
    NSEventMaskKeyDown: int | None = appkit.NSEventMaskKeyDown
    NSEventMaskKeyUp: int | None = appkit.NSEventMaskKeyUp
    NSEventModifierFlagCommand: int | None = appkit.NSEventModifierFlagCommand
    NSEventModifierFlagControl: int | None = appkit.NSEventModifierFlagControl
    NSEventModifierFlagOption: int | None = appkit.NSEventModifierFlagOption
    NSEventModifierFlagShift: int | None = appkit.NSEventModifierFlagShift
else:
    NSEvent: _NSEventClass | None = None
    NSEventMaskKeyDown: int | None = None
    NSEventMaskKeyUp: int | None = None
    NSEventModifierFlagCommand: int | None = None
    NSEventModifierFlagControl: int | None = None
    NSEventModifierFlagOption: int | None = None
    NSEventModifierFlagShift: int | None = None

if _Quartz is not None:
    quartz = cast(_QuartzModule, _Quartz)
    CGEventCreateKeyboardEvent: Callable[[object | None, int, bool], object] | None = (
        quartz.CGEventCreateKeyboardEvent
    )
    CGEventPost: Callable[[int, object], None] | None = quartz.CGEventPost
    kCGHIDEventTap: int | None = quartz.kCGHIDEventTap
else:
    CGEventCreateKeyboardEvent: Callable[[object | None, int, bool], object] | None = None
    CGEventPost: Callable[[int, object], None] | None = None
    kCGHIDEventTap: int | None = None


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
_KEY_CODE_TO_TOKEN = {code: token for token, code in _MAC_KEY_CODES.items()}


def native_keyboard_backend_available() -> bool:
    if sys.platform != "darwin":
        return False
    if _AppKit is None or _Quartz is None or _ApplicationServices is None:
        return False
    input_ok = macos_keyboard_input_permission_granted()
    injection_ok = macos_keyboard_injection_permission_granted()
    available = (
        NSEvent is not None
        and CGEventCreateKeyboardEvent is not None
        and CGEventPost is not None
        and kCGHIDEventTap is not None
        and input_ok
        and injection_ok
    )
    return available


def macos_keyboard_input_permission_granted() -> bool:
    if sys.platform != "darwin" or _Quartz is None:
        return False
    quartz = cast(_QuartzModule, _Quartz)
    preflight = getattr(quartz, "CGPreflightListenEventAccess", None)
    if preflight is None:
        return False
    try:
        granted = bool(preflight())
        return granted
    except Exception:
        return False


def macos_keyboard_injection_permission_granted() -> bool:
    if sys.platform != "darwin" or _ApplicationServices is None:
        return False
    services = cast(_ApplicationServicesModule, _ApplicationServices)
    trusted = getattr(services, "AXIsProcessTrustedWithOptions", None)
    prompt_option = getattr(services, "kAXTrustedCheckOptionPrompt", None)
    if trusted is None or prompt_option is None:
        return False
    try:
        granted = bool(trusted({prompt_option: False}))
        return granted
    except Exception:
        return False


def request_macos_keyboard_permissions() -> None:
    if sys.platform != "darwin":
        return

    if _Quartz is not None:
        quartz = cast(_QuartzModule, _Quartz)
        request_listen = getattr(quartz, "CGRequestListenEventAccess", None)
        if request_listen is not None:
            try:
                request_listen()
            except Exception:
                pass

    if _ApplicationServices is not None:
        services = cast(_ApplicationServicesModule, _ApplicationServices)
        trusted = getattr(services, "AXIsProcessTrustedWithOptions", None)
        prompt_option = getattr(services, "kAXTrustedCheckOptionPrompt", None)
        if trusted is not None and prompt_option is not None:
            try:
                trusted({prompt_option: True})
            except Exception:
                pass


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


def _event_modifiers(event: _KeyboardEvent) -> frozenset[str]:
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


def _event_key_token(event: _KeyboardEvent) -> str:
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
    handles: list[object]

    def stop(self) -> None:
        if not native_keyboard_backend_available():
            self.handles.clear()
            return
        event_class = cast(_NSEventClass, NSEvent)
        for handle in self.handles:
            try:
                event_class.removeMonitor_(handle)
            except Exception:
                pass
                pass
        self.handles.clear()


def register_hotkey(
    bind_str: str, callback: Callable[[], object | None]
) -> NativeMonitorHandle | None:
    if not native_keyboard_backend_available():
        return None

    required_modifiers, required_key = _normalize_hotkey(bind_str)

    def handle_event(event: _KeyboardEvent) -> None:
        try:
            if getattr(event, "isARepeat", lambda: False)():
                return
            event_key = _event_key_token(event)
            event_modifiers = _event_modifiers(event)
            if event_key != required_key:
                return
            if event_modifiers != required_modifiers:
                return
            dispatch_to_main_thread(callback)
        except Exception:
            traceback.print_exc()

    event_class = cast(_NSEventClass, NSEvent)
    key_down_mask = cast(int, NSEventMaskKeyDown)
    monitor = event_class.addGlobalMonitorForEventsMatchingMask_handler_(
        key_down_mask, handle_event
    )
    return NativeMonitorHandle([monitor])


def register_key_listeners(
    keys: Sequence[str],
    on_press: Callable[[str], None],
    on_release: Callable[[str], None],
) -> NativeMonitorHandle | None:
    if not native_keyboard_backend_available():
        return None

    normalized_keys = {key.lower(): key for key in keys}

    def handle_press(event: _KeyboardEvent) -> None:
        try:
            key_token = _event_key_token(event)
            if key_token in normalized_keys:
                key_name = normalized_keys[key_token]
                dispatch_to_main_thread(lambda key_name=key_name: on_press(key_name))
        except Exception:
            traceback.print_exc()

    def handle_release(event: _KeyboardEvent) -> None:
        try:
            key_token = _event_key_token(event)
            if key_token in normalized_keys:
                key_name = normalized_keys[key_token]
                dispatch_to_main_thread(lambda key_name=key_name: on_release(key_name))
        except Exception:
            traceback.print_exc()

    event_class = cast(_NSEventClass, NSEvent)
    key_down_mask = cast(int, NSEventMaskKeyDown)
    key_up_mask = cast(int, NSEventMaskKeyUp)
    press_monitor = event_class.addGlobalMonitorForEventsMatchingMask_handler_(
        key_down_mask, handle_press
    )
    release_monitor = event_class.addGlobalMonitorForEventsMatchingMask_handler_(
        key_up_mask, handle_release
    )
    return NativeMonitorHandle([press_monitor, release_monitor])


def press_and_release(key_name: str) -> None:
    if not native_keyboard_backend_available():
        raise RuntimeError("Native macOS keyboard backend is unavailable.")

    key_code = _MAC_KEY_CODES.get(key_name.lower())
    if key_code is None:
        raise ValueError(f"Unsupported macOS key: {key_name}")

    quartz = cast(_QuartzModule, _Quartz)
    create_keyboard_event = cast(
        Callable[[object | None, int, bool], object], CGEventCreateKeyboardEvent
    )
    post_event = cast(Callable[[int, object], None], CGEventPost)
    hid_tap = cast(int, kCGHIDEventTap)
    down_event = create_keyboard_event(None, key_code, True)
    up_event = create_keyboard_event(None, key_code, False)
    post_event(hid_tap, down_event)
    post_event(hid_tap, up_event)

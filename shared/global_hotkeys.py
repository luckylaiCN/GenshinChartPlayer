from __future__ import annotations

import time
import threading
from typing import Callable, Dict, FrozenSet

from pynput import keyboard
from pynput.keyboard import Key, KeyCode
import traceback


def _normalize_key(key) -> str:
    if isinstance(key, KeyCode):
        return (key.char or "").lower()
    if isinstance(key, Key):
        name = key.name
        if name is None:
            return ""
        return name.lower()
    return str(key).lower()


class GlobalHotkeyManager:
    def __init__(self):
        self._listener = None
        # Use RLock to allow re-entrant calls (register_hotkey calls start())
        self._lock = threading.RLock()
        self._pressed: set[str] = set()
        self._hotkeys: Dict[FrozenSet[str], Dict] = {}
        # per-key down/up listeners
        self._down_listeners: Dict[str, list[Callable[[], None]]] = {}
        self._up_listeners: Dict[str, list[Callable[[], None]]] = {}
        self._last_trigger: Dict[FrozenSet[str], float] = {}

    def start(self):
        with self._lock:
            if self._listener is not None:
                return
            def on_press(key):
                k = _normalize_key(key)
                if k:
                    first_press = k not in self._pressed
                    self._pressed.add(k)
                    # call down listeners only on first press
                    if first_press:
                        for cb in list(self._down_listeners.get(k, [])):
                            try:
                                cb()
                            except Exception:
                                traceback.print_exc()
                self._check_hotkeys()

            def on_release(key):
                k = _normalize_key(key)
                with self._lock:
                    if k in self._pressed:
                        self._pressed.remove(k)
                        for cb in list(self._up_listeners.get(k, [])):
                            try:
                                cb()
                            except Exception:
                                traceback.print_exc()
            self._listener = keyboard.Listener(on_press=on_press, on_release=on_release)
            self._listener.daemon = True
            self._listener.start()

    def stop(self):
        with self._lock:
            if self._listener is not None:
                self._listener.stop()
                self._listener = None
                self._pressed.clear()

    def register_hotkey(self, hotkey: str, callback: Callable[[], None], debounce: float = 0.3):
        """
        Register a hotkey. hotkey: string like 'ctrl+shift+f5' or 'f12' (case-insensitive)
        """
        parts = [p.strip().lower() for p in hotkey.replace("+", "+").split("+") if p.strip()]
        keyset = frozenset(parts)
        with self._lock:
            self._hotkeys[keyset] = {"callback": callback, "debounce": debounce}
            self._last_trigger.setdefault(keyset, 0.0)
            try:
                self.start()
            except Exception:
                traceback.print_exc()

    def unregister_hotkey(self, hotkey: str):
        parts = [p.strip().lower() for p in hotkey.replace("+", "+").split("+") if p.strip()]
        keyset = frozenset(parts)
        with self._lock:
            self._hotkeys.pop(keyset, None)
            self._last_trigger.pop(keyset, None)

    def register_key_down(self, key: str, callback: Callable[[], None]):
        k = key.strip().lower()
        with self._lock:
            self._down_listeners.setdefault(k, []).append(callback)
            try:
                self.start()
            except Exception:
                traceback.print_exc()

    def unregister_key_down(self, key: str, callback: Callable[[], None]):
        k = key.strip().lower()
        with self._lock:
            if k in self._down_listeners:
                try:
                    self._down_listeners[k].remove(callback)
                except ValueError:
                    pass

    def register_key_up(self, key: str, callback: Callable[[], None]):
        k = key.strip().lower()
        with self._lock:
            self._up_listeners.setdefault(k, []).append(callback)
            try:
                self.start()
            except Exception:
                traceback.print_exc()

    def unregister_key_up(self, key: str, callback: Callable[[], None]):
        k = key.strip().lower()
        with self._lock:
            if k in self._up_listeners:
                try:
                    self._up_listeners[k].remove(callback)
                except ValueError:
                    pass

    def _check_hotkeys(self):
        now = time.time()
        with self._lock:
            pressed = set(self._pressed)
            for keyset, info in list(self._hotkeys.items()):
                if keyset.issubset(pressed):
                    last = self._last_trigger.get(keyset, 0)
                    if now - last >= info.get("debounce", 0.3):
                        # trigger
                        try:
                            info["callback"]()
                        except Exception:
                            import traceback

                            traceback.print_exc()
                        self._last_trigger[keyset] = now


# Module-level singleton
_manager = GlobalHotkeyManager()


def register_hotkey(hotkey: str, callback: Callable[[], None], debounce: float = 0.3):
    _manager.register_hotkey(hotkey, callback, debounce)


def unregister_hotkey(hotkey: str):
    _manager.unregister_hotkey(hotkey)


def register_key_down(key: str, callback: Callable[[], None]):
    _manager.register_key_down(key, callback)


def unregister_key_down(key: str, callback: Callable[[], None]):
    _manager.unregister_key_down(key, callback)


def register_key_up(key: str, callback: Callable[[], None]):
    _manager.register_key_up(key, callback)


def unregister_key_up(key: str, callback: Callable[[], None]):
    _manager.unregister_key_up(key, callback)


def start_listener():
    _manager.start()


def stop_listener():
    _manager.stop()

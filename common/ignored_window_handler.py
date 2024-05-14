"""handler for ignored windows. creates an interface to easily manage the ignored windows"""

import threading
import time
from typing import Set

import pyautogui
from pygetwindow import Win32Window  # type: ignore[import-untyped]

from common.tools import get_window_hwnd


class IgnoredWindowsHandler:
    """creates an interface to easily manage the ignored windows"""

    def __init__(self) -> None:
        self.__ignored_windows: Set[int] = set()

    def is_ignored(self, window_hwnd: int) -> bool:
        """return whether given window is ignored"""

        return window_hwnd in self.__ignored_windows

    def ignore(self, window: Win32Window) -> None:
        """add this window as an ignored window and wait in the background until is it closed."""

        self.__ignored_windows.add(get_window_hwnd(window))
        threading.Thread(target=self._cleanup_on_close, args=(window,)).start()

    def _cleanup_on_close(self, window: Win32Window) -> None:
        while window in pyautogui.getAllWindows():  # type: ignore[attr-defined]
            time.sleep(5)

        self.__ignored_windows.remove(get_window_hwnd(window))

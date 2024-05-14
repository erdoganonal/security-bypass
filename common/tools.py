"""Common function/methods"""
import psutil
import pyautogui
from pygetwindow import Win32Window  # type: ignore[import-untyped]
from tendo import singleton

from common.exit_codes import ExitCodes

_GLOBAL = {}


def is_windows_locked() -> bool:
    """Return the lock information of the windows"""

    for proc in psutil.process_iter():
        if proc.name() == "LogonUI.exe":
            return True
    return False


class InplaceInt:
    """an integer that the value of it can be changed(mutable)"""

    def __init__(self, value: int = 0) -> None:
        self._value = value

    def get(self) -> int:
        """return the value of this instance"""

        return self._value

    def set(self, value: int = 0) -> None:
        """set the value to given one"""

        self._value = value

    def get_and_increment(self, by: int = 0) -> int:
        """return the value and increment by given value"""

        value = self._value
        self._value += by
        return value

    def increment_and_get(self, by: int = 0) -> int:
        """increment by given value and return"""

        self._value += by
        return self._value


def split_long_string(input_string: str, max_length: int) -> str:
    """Splits a long string into smaller pieces based on the given maximum length,
    ensuring that the split occurs at spaces and not in the middle of words.

    Args:
    - input_string (str): The input string to be split.
    - max_length (int): The maximum length for each divided piece.

    Returns:
    - str: A string with line breaks inserted where necessary to fit within
      the specified maximum length.
    """

    if len(input_string) <= max_length:
        return input_string

    lines = []
    start = 0

    while start < len(input_string):
        end = start + max_length

        # Adjust end index to the last space within the limit
        if end < len(input_string) and input_string[end] != " ":
            while end > start and input_string[end] != " ":
                end -= 1

        lines.append(input_string[start:end].strip())
        start = end + 1

    return "\n".join(lines)


def check_single_instance() -> None:
    """Check if a single instance is running"""

    try:
        _GLOBAL["singleton"] = singleton.SingleInstance()  # type: ignore[no-untyped-call]
    except singleton.SingleInstanceException:
        ExitCodes.ALREADY_RUNNING.exit()


def get_window_by_hwnd(hwnd: int) -> Win32Window | None:
    """return the window by given ID"""

    try:
        return next(window for window in pyautogui.getAllWindows() if get_window_hwnd(window) == hwnd)  # type: ignore[attr-defined]
    except StopAsyncIteration:
        return None


def get_window_hwnd(window: Win32Window) -> int:
    """return the ID of the window"""

    # pylint: disable=protected-access
    return window._hWnd  # type: ignore[no-any-return]

"""Common function/methods"""

import os
from functools import cache
from typing import TYPE_CHECKING, Type

import psutil
import pyautogui
from pygetwindow import Win32Window  # type: ignore[import-untyped]
from screeninfo import get_monitors
from tendo import singleton

from common.exit_codes import ExitCodes
from settings import DBG_ENV_NAME, WRAPPER_FILE
from updater.helpers import restart

if TYPE_CHECKING:
    import pywinauto  # type: ignore[import-untyped]

_GLOBAL = {}


@cache
def is_debug_enabled() -> bool:
    """Return the debug status"""

    return bool(os.getenv(DBG_ENV_NAME, None))


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
    except StopIteration:
        return None


def get_window_hwnd(window: Win32Window) -> int:
    """return the ID of the window"""

    # pylint: disable=protected-access
    return window._hWnd  # type: ignore[no-any-return]


def focus_window(window: Win32Window) -> None:
    """focus on given window by minimizing and maximizing it"""

    left, top, width, height = window.left, window.top, window.width, window.height

    window.minimize()
    window.maximize()

    window.resizeTo(width, height)
    window.moveTo(left, top)


def get_position(window: Win32Window) -> tuple[int, int]:
    """return the passkey window position based on given window"""

    tolerance = 180
    left_shift = 10
    last_monitor = get_monitors()[-1]

    if (window.left + window.width + tolerance) > (last_monitor.x + last_monitor.width):
        return window.left + left_shift, window.top
    return window.left + window.width, window.top


def _get_pywinauto() -> "pywinauto":
    # workaround for: https://github.com/pywinauto/pywinauto/issues/472
    import pywinauto  # pylint: disable=import-outside-toplevel

    return pywinauto


def get_window(window_or_id: Win32Window | int | str) -> "pywinauto.application.WindowSpecification":
    """return the window based on given ID or window object"""
    pywinauto = _get_pywinauto()

    desktop = pywinauto.Desktop(backend="uia")
    if isinstance(window_or_id, Win32Window):
        window_id = get_window_hwnd(window_or_id)
    else:
        window_id = int(window_or_id)

    window = desktop.window(handle=window_id)

    return window


def _extract_text_from_window(
    window: "pywinauto.application.WindowSpecification",
    kind: "Type[pywinauto.controls.uiawrapper.UIAWrapper]",
) -> str:
    text = ""
    try:
        # Get the text of the current window
        if isinstance(window, kind):
            text += window.window_text() + "\n"
    except Exception:  # pylint: disable=broad-except
        pass

    # Recursively search for child windows
    for child in window.children():
        text += _extract_text_from_window(child, kind=kind)

    return text


def extract_text_from_window(window_or_id: Win32Window | int | str) -> str:
    """recursively search for child windows and extract text"""
    pywinauto = _get_pywinauto()

    window = get_window(window_or_id)
    return _extract_text_from_window(window, kind=pywinauto.controls.uia_controls.StaticWrapper)


def get_password_length(window_or_id: Win32Window) -> int:
    """return the password length based on given window"""
    pywinauto = _get_pywinauto()

    window = get_window(window_or_id)

    chars = _extract_text_from_window(window, kind=pywinauto.controls.uia_controls.EditWrapper)
    return len(chars.strip())


def complete_update() -> None:
    """Complete the update process"""

    try:
        del _GLOBAL["singleton"]
    except KeyError:
        pass

    generate_wrapper_file()

    restart()


def generate_wrapper_file() -> None:
    """generate the wrapper file"""

    content = '''"""wrapper for the main application to catch unhandled exceptions"""

import time
import traceback

try:
    from security_bypass_tray import main

    main()
except Exception as e:
    traceback.print_exception(e)
    with open("error.log", "a+", encoding="utf-8") as error_fd:
        error_fd.write(f"{time.time()} - {e}\\n")

    raise SystemExit(1) from e
'''

    with open(WRAPPER_FILE, "w", encoding="utf-8") as wrapper_fd:
        wrapper_fd.write(content)

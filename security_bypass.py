"""Allows you to save passwords and let you to bypass the windows security windows
 by entering the passwords automatically"""

import threading
import time
from typing import Generator, List, NoReturn, Set

import pyautogui
import pyperclip  # type: ignore[import-untyped]
from pygetwindow import Win32Window  # type: ignore[import-untyped]
from tendo import singleton

from common.exit_codes import ExitCodes
from common.tools import InplaceInt, is_windows_locked
from config import ConfigManager
from config.config import WindowConfig
from config.config_key_manager import FROM_ENV, NOT_SET, check_config_file, validate_and_get_mk
from notification_handler.base import NotificationHandlerBase
from notification_handler.cli import CLINotificationHandler
from notification_handler.gui import GUINotificationHandler
from password_manager import __name__ as pwd_manager_name
from select_window_info.base import SelectWindowInfoBase, WindowInfo
from select_window_info.cli import CLISelectWindowInfo
from select_window_info.gui import GUISelectWindowInfo
from settings import ASK_PASSWORD_ON_LOCK, CREDENTIALS_FILE, GUI, MIN_SLEEP_SECS_AFTER_KEY_SENT

SLEEP_SECS = 1


def main() -> None:
    """starts from here"""
    if GUI:
        security_bypass = SecurityBypass(GUISelectWindowInfo(), GUINotificationHandler())
    else:
        security_bypass = SecurityBypass(CLISelectWindowInfo(), CLINotificationHandler(message_format="{message}"))
    security_bypass.start()


class SecurityBypass:
    """Allows you to save passwords and let you to bypass the windows security windows
    by entering the passwords automatically"""

    def __init__(self, select_window: SelectWindowInfoBase, notification_handler: NotificationHandlerBase) -> None:
        self._loop = False
        self._select_window_info_func = select_window.select
        self._notification_handler = notification_handler
        self.__key: bytes | None = None

        self._windows = self.__get_windows()
        self._credential_file_modified_time = 0.0
        self.__window_hwnd_s: Set[int] = set()

    def _exit(self, exit_code: ExitCodes) -> NoReturn:
        self._loop = False
        exit_code.exit()

    def __get_windows(self, show_error: bool = True) -> List[WindowConfig]:
        which = InplaceInt()

        while True:
            try:
                which.set(NOT_SET)
                self.__key = self.__key or validate_and_get_mk(which=which)
                check_config_file()
                return ConfigManager(key=self.__key).get_config().windows
            except ValueError:
                self.__key = None
                if show_error:
                    self._notification_handler.critical("Cannot load configurations. The Master Key is wrong.")
                if which.get() == FROM_ENV:
                    # if the passkey is coming from the environment variable, and it was wrong;
                    # do not try to get it. It goes endless loop, otherwise.
                    self._exit(ExitCodes.WRONG_MASTER_KEY)
                show_error = True
                continue
            except KeyError as err:
                self._notification_handler.error(err.args[0])
                self._exit(ExitCodes.EMPTY_MASTER_KEY)
            except FileNotFoundError:
                self._notification_handler.error(f"The credentials file does not exist. Use '{pwd_manager_name}' to create it.")
                self._exit(ExitCodes.CREDENTIAL_FILE_DOES_NOT_EXISTS)

    def _sleep(self, secs: int = 0) -> None:
        if secs == 0:
            secs = SLEEP_SECS
        elif secs < 0:
            raise ValueError("Time travel did not invent yet!")

        sleep_secs = 0
        while sleep_secs < secs and self._loop:
            sleep_secs += 1
            time.sleep(1)

    def _handle_windows_lock(self) -> None:
        if not is_windows_locked():
            return

        while is_windows_locked():
            time.sleep(1)

        self._notification_handler.warning("Windows is locked. The password must be provided.")
        self._windows = self.__get_windows()

    def _reload_config_in_bg(self) -> None:
        while self._loop:
            self._reload_if_required()
            time.sleep(1)

    def _reload_if_required(self) -> None:
        credential_file_modified_time = CREDENTIALS_FILE.stat().st_mtime
        if credential_file_modified_time != self._credential_file_modified_time:
            self._windows = self.__get_windows(show_error=False)
            self._credential_file_modified_time = credential_file_modified_time

    def _select(self) -> None:
        windows = list(self.filter_windows())
        if not windows:
            return  # no matching window found

        window_hwnd = windows[0].window._hWnd  # pylint: disable=protected-access
        if window_hwnd in self.__window_hwnd_s:
            return  # already processing

        self.__window_hwnd_s.add(window_hwnd)
        window_info = self._select_window_info_func(windows)

        if window_info is not None:
            self.send_keys(*window_info)
            # Do not sleep less than `MIN_SLEEP_SECS_AFTER_KEY_SENT` seconds if a key is sent
            if SLEEP_SECS < MIN_SLEEP_SECS_AFTER_KEY_SENT:
                self._sleep(MIN_SLEEP_SECS_AFTER_KEY_SENT)

        self.__window_hwnd_s.remove(window_hwnd)

    def _start(self) -> None:
        self._loop = True

        self._notification_handler.debug("Application is started.")
        threading.Thread(target=self._reload_config_in_bg, daemon=True).start()

        while self._loop:
            if ASK_PASSWORD_ON_LOCK:
                self._handle_windows_lock()

            threading.Thread(target=self._select, daemon=True).start()

            self._sleep()

    def start(self) -> None:
        """start the window listener"""
        try:
            self._start()
        except KeyboardInterrupt:
            self._notification_handler.warning("An interrupt detected. Terminating the app..")

        self._notification_handler.info("App is terminated!")

    @classmethod
    def focus_window(cls, window: Win32Window) -> None:
        """Bring focus to given window"""
        window.minimize()
        window.maximize()

    @classmethod
    def send_keys(cls, window: Win32Window, keys: str) -> None:
        """Send given keys to the given window"""
        cls.focus_window(window)

        send_enter = keys.endswith("\n")

        current_clipboard = pyperclip.paste()

        pyperclip.copy(keys[:-1] if send_enter else keys)
        pyautogui.hotkey("ctrl", "v")

        pyperclip.copy(current_clipboard)

        if send_enter:
            pyautogui.write("\n")

    def filter_windows(self) -> Generator[WindowInfo, None, None]:
        """Filter the windows by title"""

        break_loop = False
        for window in pyautogui.getAllWindows():  # type: ignore[attr-defined]
            for window_info in self._windows:
                if (window_info.pattern is not None and window_info.pattern.match(window.title)) or window_info.title == window.title:
                    break_loop = True
                    yield WindowInfo(window.title, window_info.name, window_info.passkey, window_info.group, window)

            if break_loop:
                break


if __name__ == "__main__":
    try:
        me = singleton.SingleInstance()  # type: ignore[no-untyped-call]
    except singleton.SingleInstanceException:
        ExitCodes.ALREADY_RUNNING.exit()

    main()

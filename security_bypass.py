"""Allows you to save passwords and let you to bypass the windows security windows
 by entering the passwords automatically"""

import sys
import time
from typing import Generator, List

import pyautogui
import pyperclip  # type: ignore[import-untyped]
from pygetwindow import Win32Window  # type: ignore[import-untyped]
from tendo import singleton

from common.tools import is_windows_locked
from config import ConfigManager
from config.config import WindowConfig
from config.config_key_manager import check_config_file, validate_and_get_mk
from notification_handler.base import NotificationHandlerBase
from notification_handler.cli import CLINotificationHandler
from notification_handler.gui import GUINotificationHandler
from password_manager import __name__ as pwd_manager_name
from select_window_info.base import SelectWindowInfoBase, WindowInfo
from select_window_info.cli import CLISelectWindowInfo
from select_window_info.gui import GUISelectWindowInfo
from settings import ASK_PASSWORD_ON_LOCK, GUI, MIN_SLEEP_SECS_AFTER_KEY_SENT, PASSWORD_REQUIRED_FILE_PATH, RELOAD_REQUIRED_FILE_PATH


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
        self.sleep_secs = 1
        self._notification_handler = notification_handler
        self.__key: bytes | None = None

        self._windows = self.__get_windows()

    def __get_windows(self) -> List[WindowConfig]:
        self.__key = self.__key or validate_and_get_mk()
        while True:
            try:
                check_config_file()
                return ConfigManager(key=self.__key).get_config().windows
            except ValueError:
                self._notification_handler.critical("Cannot load configurations. The Master Key is wrong.")
                continue
            except KeyError as err:
                self._notification_handler.error(err.args[0])
                sys.exit(1)
            except FileNotFoundError:
                self._notification_handler.error(f"The credentials file does not exist. Use '{pwd_manager_name}' to create it.")
                sys.exit(1)

    def _sleep(self, secs: int = 0) -> None:
        if secs == 0:
            secs = self.sleep_secs
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

    def _reload_if_required(self) -> None:
        if RELOAD_REQUIRED_FILE_PATH.exists():
            if PASSWORD_REQUIRED_FILE_PATH.exists():
                self.__key = None
            self._windows = self.__get_windows()

        RELOAD_REQUIRED_FILE_PATH.unlink(missing_ok=True)
        PASSWORD_REQUIRED_FILE_PATH.unlink(missing_ok=True)

    def _start(self) -> None:
        self._loop = True

        self._notification_handler.debug("Application is started.")

        while self._loop:
            if ASK_PASSWORD_ON_LOCK:
                self._handle_windows_lock()

            self._reload_if_required()

            windows = self.filter_windows()
            window_info = self._select_window_info_func(windows)
            if window_info is not None:
                self.send_keys(*window_info)
                # Do not sleep less than `MIN_SLEEP_SECS_AFTER_KEY_SENT` seconds if a key is sent
                if self.sleep_secs < MIN_SLEEP_SECS_AFTER_KEY_SENT:
                    self._sleep(MIN_SLEEP_SECS_AFTER_KEY_SENT)

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

        for window in pyautogui.getAllWindows():  # type: ignore[attr-defined]
            for window_info in self._windows:
                if window_info.pattern.match(window.title):
                    yield WindowInfo(window.title, window, window_info.passkey_data)
                    break


if __name__ == "__main__":
    try:
        me = singleton.SingleInstance()  # type: ignore[no-untyped-call]
    except singleton.SingleInstanceException:
        sys.exit(2)

    main()

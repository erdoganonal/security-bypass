"""Allows you to save passwords and let you to bypass the windows security windows
 by entering the passwords automatically"""

import sys
import time
from typing import Generator

import pyautogui
import pyperclip  # type: ignore[import]
from pygetwindow import Win32Window  # type: ignore[import]

from config import ConfigManager
from config.config_key_manager import validate_and_get_mk
from notification_handler.base import NotificationHandlerBase
from notification_handler.cli import CLINotificationHandler
from select_window_info.base import SelectWindowInfoBase, WindowInfo
from select_window_info.cli import CLISelectWindowInfo
from select_window_info.gui import GUISelectWindowInfo
from settings import GUI


def main() -> None:
    """starts from here"""
    if GUI:
        security_bypass = SecurityBypass(GUISelectWindowInfo(), CLINotificationHandler(message_format="{message}"))
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

        try:
            self._windows = ConfigManager(key=validate_and_get_mk()).get_config().windows
        except ValueError:
            self._notification_handler.critical("Cannot load configurations. The Master Key is wrong.")
            sys.exit(1)
        except KeyError as err:
            self._notification_handler.error(err.args[0])
            sys.exit(1)

    def _sleep(self) -> None:
        sleep_secs = 0
        while sleep_secs < self.sleep_secs and self._loop:
            sleep_secs += 1
            time.sleep(1)

    def _start(self) -> None:
        self._loop = True

        while self._loop:
            windows = self.filter_windows()
            window_info = self._select_window_info_func(windows)
            if window_info is not None:
                self.send_keys(*window_info)

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

        pyperclip.copy(keys[:-1] if send_enter else keys)
        pyautogui.hotkey("ctrl", "v")

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
    main()

"""Allows you to save passwords and let you to bypass the windows security windows
by entering the passwords automatically"""

import threading
import time
import traceback
from dataclasses import dataclass, field
from functools import cache
from typing import List, NoReturn, Set

import pyautogui
import pyperclip  # type: ignore[import-untyped]
from pygetwindow import Win32Window  # type: ignore[import-untyped]

from common import exceptions
from common.auto_key_trigger_manager import AutoKeyTriggerManager
from common.exit_codes import ExitCodes
from common.ignored_window_handler import IgnoredWindowsHandler
from common.tools import (
    check_config_file,
    check_single_instance,
    complete_update,
    extract_text_from_window,
    get_password_length,
    get_window_hwnd,
    is_interactive_authentication,
    is_windows_locked,
    restart_as_admin,
)
from communication import data_sharing
from config import ConfigManager
from config.config import WindowData
from handlers.authentication.base import AuthenticationController
from handlers.notification.base import NotificationController
from handlers.notification.gui import NotificationGUI
from handlers.window_selector.base import WindowSelectorController
from handlers.window_selector.pyqt_gui import WindowSelectorPyQtGUI
from helpers.user_preferences import UserPreferencesAccessor
from logger import initialize as logger_initialize
from logger import logger
from package_builder.registry import PBId, PBRegistry
from settings import ASK_PASSWORD_ON_LOCK, CREDENTIALS_FILE, DEBUG, MAX_KEY_SENT_ATTEMPTS, MIN_SLEEP_SECS_AFTER_KEY_SENT
from updater.helpers import check_for_updates

SLEEP_SECS = 1

TEMP_WARNING_TIMEOUT = 150
TEMP_WARNING_AUTO_CLOSE_MSG = (
    f"\n\nThis message will be deleted after {TEMP_WARNING_TIMEOUT} seconds and the password selection window will be opened."
)


def main() -> None:
    """starts from here"""
    logger_initialize()

    user_preferences = UserPreferencesAccessor.get()
    if user_preferences.auth_method.is_admin_rights_required and is_interactive_authentication():
        restart_as_admin()

    PBRegistry.register_safe(PBId.NOTIFICATION_HANDLER, NotificationController(NotificationGUI()))
    PBRegistry.register_safe(PBId.SELECT_WINDOW, WindowSelectorController(WindowSelectorPyQtGUI()))
    PBRegistry.register_safe(PBId.AUTHENTICATION_HANDLER, AuthenticationController(user_preferences.auth_method))

    PBRegistry.check_all_registered()

    if check_for_updates(report_error=False):
        complete_update()

    security_bypass = SecurityBypass()
    try:
        security_bypass.start()
    except exceptions.ToolError as e:
        PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController).error(e.message, title="Error occurred.")
        e.exit()

    ExitCodes.SUCCESS.exit()


@dataclass
class _WindowData:
    windows: List[WindowData] = field(default_factory=list)
    window_hwnd_s: Set[int] = field(default_factory=set)
    ignored_windows_handler: IgnoredWindowsHandler = field(default_factory=IgnoredWindowsHandler)
    auto_key_trigger_manager: AutoKeyTriggerManager = field(default_factory=AutoKeyTriggerManager)


class SecurityBypass:
    """Allows you to save passwords and let you to bypass the windows security windows
    by entering the passwords automatically"""

    def __init__(self) -> None:
        self._is_running = False
        self.__key: bytes | None = None

        self._credential_file_modified_time = 0.0
        self._window_data = _WindowData()

        key_tracker = data_sharing.Informer(data_sharing.KEY_TRACKER_PORT)
        key_tracker.add_callback(self._on_master_key_change)
        key_tracker.start_server()

    def _on_master_key_change(self, data: bytes) -> None:
        self.__key = data
        logger.info("Master key has been changed.")

    def _exit(self, exit_code: ExitCodes) -> NoReturn:
        logger.debug("Exiting the application.")
        self._is_running = False
        exit_code.exit()

    def _set_temp_timeout(self) -> None:
        notification_controller = PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController)
        if isinstance(notification_controller, NotificationGUI):
            notification_controller.set_temp_timeout(TEMP_WARNING_TIMEOUT * 1000)

    def _load_config(self) -> None:
        logger.debug("Loading the config file.")
        check_config_file()

        self.__key = self.__key or PBRegistry.get_typed(PBId.AUTHENTICATION_HANDLER, AuthenticationController).get_master_key()

        if not self.__key:
            raise exceptions.EmptyMasterKeyError()

        if not isinstance(self.__key, bytes):
            raise exceptions.WrongMasterKeyFormat(self.__key.__class__.__name__)

        try:
            self._window_data.windows = ConfigManager(key=self.__key).get_config().windows
        except ValueError as exc:
            raise exceptions.WrongMasterKeyError() from exc

        self._credential_file_modified_time = CREDENTIALS_FILE.stat().st_mtime
        logger.info("Config file has been loaded successfully.")

    def _sleep(self, secs: int = 0) -> None:
        if secs == 0:
            secs = SLEEP_SECS
        elif secs < 0:
            raise ValueError("Time travel did not invent yet!")

        sleep_secs = 0
        while sleep_secs < secs and self._is_running:
            sleep_secs += 1
            time.sleep(1)

    def _handle_windows_lock(self) -> None:
        if not is_windows_locked():
            return

        while is_windows_locked():
            time.sleep(1)

        PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController).warning("Windows is locked. Authentication is required.")
        self._load_config()

    def _reload_config_in_bg(self) -> None:
        while self._is_running:
            self._reload_if_required()
            time.sleep(1)

    def _reload_if_required(self) -> None:
        credential_file_modified_time = CREDENTIALS_FILE.stat().st_mtime
        if credential_file_modified_time != self._credential_file_modified_time:
            logger.debug("Config file has been modified. Reloading the config.")
            UserPreferencesAccessor.load()
            try:
                self._load_config()
            except exceptions.WrongMasterKeyError:
                # this case should not happen. In case if happens for some reason,
                # let's try to reload the config again in next cycle of background loader.
                logger.error("Master key is incorrect. Trying to reload the config in the next cycle.")
                return
            self._credential_file_modified_time = credential_file_modified_time
            logger.info("Config file has been reloaded successfully.")

    @staticmethod
    @cache
    def _extract_text_from_window_cached(window_hwnd: int) -> str:
        return extract_text_from_window(window_hwnd)

    def _auto_detect_passkey(self, window_hwnd: int, windows: list[WindowData]) -> WindowData | None:
        text = self._extract_text_from_window_cached(window_hwnd)
        auto_detected = [
            window_data
            for window_data in windows
            if (window_data.auto_key_trigger_pattern is not None and window_data.auto_key_trigger_pattern.match(text))
            or (window_data.auto_key_trigger and window_data.auto_key_trigger in text)
        ]

        notification_controller = PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController)

        if len(auto_detected) == 1:
            if self._window_data.auto_key_trigger_manager.is_already_triggered(auto_detected[0]):
                if UserPreferencesAccessor.get().repeated_window_protection:
                    user_response = notification_controller.ask_yes_no(
                        "The key has already been automatically sent to the window but either it didn't help.\n"
                        "This may be due to an incorrect password or a sync problem. "
                        "Please select the correct key from the list to avoid "
                        "potential system blockage due to multiple incorrect entries.\n\n"
                        f"Another reason might be the same window is detected in {AutoKeyTriggerManager.TIMEOUT_SECS} seconds.\n"
                        "If you expect to see multiple windows, with check can be disabled for "
                        f"{AutoKeyTriggerManager.TIMEOUT_SECS} seconds.\n\n"
                        "Do you want to disable the check for temporarily?",
                        title="Key Already Sent",
                    )
                else:
                    user_response = True

                if user_response:
                    self._window_data.auto_key_trigger_manager.temp_disable_check(auto_detected[0])
                else:
                    return None
            else:
                self._window_data.auto_key_trigger_manager.add_triggered(auto_detected[0])
            return auto_detected[0]

        if len(auto_detected) > 1:
            self._set_temp_timeout()
            notification_controller.warning(
                f"Multiple windows are detected for matching pattern {text}. Please select one manually." + TEMP_WARNING_AUTO_CLOSE_MSG,
                title="Multiple Windows Detected",
            )
        return None

    def _select(self) -> None:
        window, windows = self.filter_windows()
        if window is None or not windows:
            return  # no matching window found

        window_hwnd = get_window_hwnd(window)
        if window_hwnd in self._window_data.window_hwnd_s:
            return  # already processing

        if self._window_data.ignored_windows_handler.is_ignored(window_hwnd):
            return

        self._window_data.window_hwnd_s.add(window_hwnd)
        if (window_data := self._auto_detect_passkey(window_hwnd, windows)) is None:
            window_data = PBRegistry.get_typed(PBId.SELECT_WINDOW, WindowSelectorController).select(window_hwnd, windows)

        if window_data is None:
            self._window_data.ignored_windows_handler.ignore(window)
        else:
            self.send_keys(window, window_data)
            # Do not sleep less than `MIN_SLEEP_SECS_AFTER_KEY_SENT` seconds if a key is sent
            if SLEEP_SECS < MIN_SLEEP_SECS_AFTER_KEY_SENT:
                self._sleep(MIN_SLEEP_SECS_AFTER_KEY_SENT)

        self._window_data.window_hwnd_s.remove(window_hwnd)

    def _start(self) -> None:
        self._is_running = True

        PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController).info("The application has been started.")
        threading.Thread(target=self._reload_config_in_bg, daemon=True).start()

        while self._is_running:
            if ASK_PASSWORD_ON_LOCK:
                self._handle_windows_lock()

            if PBRegistry.get_typed(PBId.SELECT_WINDOW, WindowSelectorController).supports_thread:
                threading.Thread(target=self._select, daemon=True).start()
            else:
                self._select()

            self._sleep()

    def start(self) -> None:
        """start the window listener in the background"""
        self._load_config()

        notification_controller = PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController)

        try:
            self._start()
        except KeyboardInterrupt:
            notification_controller.warning("An interrupt detected. Terminating the app..")
        except Exception:  # pylint: disable=broad-exception-caught
            if DEBUG:
                notification_controller.error(f"Unknown exception:: {traceback.format_exc()}", title="Unknown exception occurred.")
                raise
            logger.error("Unknown exception occurred: %s", traceback.format_exc())
            self._exit(ExitCodes.UNKNOWN)

    def stop(self, before_quit: bool = False) -> None:
        """stop the window listener"""
        self._is_running = False
        if not before_quit:
            PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController).info("The application has been stopped!")

    @property
    def is_running(self) -> bool:
        """Check if the window listener is running"""
        return self._is_running

    @classmethod
    def focus_window(cls, window: Win32Window) -> None:
        """Bring focus to given window"""
        window.minimize()
        window.maximize()

    @classmethod
    def clear_keys(cls, password_len: int) -> None:
        """Clear the keys from the password field"""
        for _ in range(password_len):
            pyautogui.press("backspace")

    @classmethod
    def _send_keys(cls, keys: str) -> None:
        pyperclip.copy(keys)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)

    @classmethod
    def _check_sent(cls, window: Win32Window, keys: str) -> bool:
        password_len = get_password_length(window)
        if password_len == len(keys):
            return True
        cls.clear_keys(password_len)
        return False

    @classmethod
    def send_keys(cls, window: Win32Window, window_data: WindowData) -> None:
        """Send given keys to the given window"""

        # backup the current clipboard content
        current_clipboard = pyperclip.paste()

        for _ in range(MAX_KEY_SENT_ATTEMPTS):
            cls.focus_window(window)
            cls._send_keys(window_data.passkey)

            if not window_data.verify_sent:
                break

            if cls._check_sent(window, window_data.passkey):
                # break the loop if the keys are sent successfully
                break
        else:
            return

        # restore the clipboard content
        pyperclip.copy(current_clipboard)

        if window_data.send_enter:
            pyautogui.press("enter")

    def filter_windows(self) -> tuple[Win32Window | None, list[WindowData]]:
        """Filter the windows by title"""

        try:
            windows: list[Win32Window] = pyautogui.getAllWindows()  # type: ignore[attr-defined]
        except OSError:
            return None, []

        for window in windows:
            windows = [
                window_data
                for window_data in self._window_data.windows
                if (window_data.title_pattern is not None and window_data.title_pattern.match(window.title))
                or window_data.title == window.title
            ]
            if windows:
                return window, windows

        return None, []


if __name__ == "__main__":
    check_single_instance()

    main()

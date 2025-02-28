"""tray version of the security bypass application"""

# pylint: disable=c-extension-no-member

import subprocess
import sys
import threading
from typing import Callable, Tuple

from PyQt6 import QtGui, QtWidgets

from common.exit_codes import ExitCodes
from common.tools import complete_update
from helpers.config_manager import ConfigManager
from notification_handler.tray import TrayNotificationHandler
from security_bypass import SecurityBypass, get_security_bypass_params
from settings import SECURITY_BYPASS_ICON, TOOL_CONFIG_FILE
from updater.helpers import check_for_updates

TITLE = "Security Bypass"

STATE_READY = f"{TITLE} [Ready]"
STATE_STOPPED = f"{TITLE} [Stopped]"
STATE_PENDING = f"{TITLE} [Pending]"
STATE_ERROR = f"{TITLE} [Error({{code}})]"
STATE_RUNNING = f"{TITLE} [Running]"

ActionType = Tuple[str, Callable[[], None] | Callable[[bool], None], bool | None]


class SecurityBypassTray:
    """Tray icon for security bypass using PyQt6."""

    def __init__(self) -> None:
        self.app = QtWidgets.QApplication(sys.argv)
        self.tray_icon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(str(SECURITY_BYPASS_ICON)), self.app)
        self.menu = QtWidgets.QMenu()

        self._action_manager = ActionManager(self)
        config = ConfigManager.get_config()

        self.add_action(("Start", self._action_manager.start, None))
        self.add_action(("Stop", self._action_manager.stop, None))
        self.add_action(("Auto start on startup", self._action_manager.toggle_auto_start, config.auto_start))
        self.add_action(None)
        self.add_action(("Check for updates", self._action_manager.check_for_updates, None))
        self.add_action(("Check updates on startup", self._action_manager.toggle_check_for_updates, config.auto_update))
        self.add_action(None)
        self.add_action(("Password Manager", self._action_manager.open_password_manager, None))
        self.add_action(
            ("Repeated Window Protection", self._action_manager.set_repeated_window_protection, config.repeated_window_protection)
        )
        self.add_action(None)
        self.add_action(("Quit", self._action_manager.quit_application, None))

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.setToolTip("Security Bypass - Stopped")
        self.tray_icon.show()

        if config.auto_update:
            self._action_manager.check_for_updates(auto=True)

        if config.auto_start:
            self._action_manager.start()
        else:
            self.state_update(TITLE, "Ready", STATE_READY)

    def add_action(self, action_or_separator: ActionType | None) -> None:
        """Add an action to the menu. If action is None, add a separator."""

        if action_or_separator is None:
            self.menu.addSeparator()
            return

        name, callback, is_checkable = action_or_separator
        action = QtGui.QAction(name, self.app)
        action.triggered.connect(callback)
        if is_checkable is not None:
            action.setCheckable(True)
            action.setChecked(is_checkable)
        self.menu.addAction(action)

    def state_update(
        self,
        title: str,
        message: str,
        hover_text: str | None = None,
        icon: QtWidgets.QSystemTrayIcon.MessageIcon = QtWidgets.QSystemTrayIcon.MessageIcon.Information,
    ) -> None:
        """Show a toast notification with the given title and message."""

        self.tray_icon.showMessage(title, message, msecs=3, icon=icon)
        if hover_text is not None:
            self.tray_icon.setToolTip(hover_text)


class ActionManager:
    """Manage the actions for the tray icon."""

    def __init__(self, tray: SecurityBypassTray) -> None:
        self._args = (get_security_bypass_params()[0], TrayNotificationHandler())
        self._instance: SecurityBypass | None = None
        self._tray = tray

    def toggle_auto_start(self, checked: bool) -> None:
        """Toggle the check for updates feature."""
        ConfigManager.partial_save(TOOL_CONFIG_FILE, auto_start=checked)

    def toggle_check_for_updates(self, checked: bool) -> None:
        """Toggle the check for updates feature."""
        ConfigManager.partial_save(TOOL_CONFIG_FILE, auto_update=checked)

    def set_repeated_window_protection(self, checked: bool) -> None:
        """Toggle the repeated window protection feature."""
        ConfigManager.partial_save(TOOL_CONFIG_FILE, repeated_window_protection=checked)

    def _get_instance(self) -> SecurityBypass | None:
        if self._instance is None:
            try:
                instance = SecurityBypass(*self._args)
            except SystemExit as error:
                self._tray.state_update(
                    TITLE,
                    "Failed to start",
                    STATE_ERROR.format(code=ExitCodes.get_name(error.code)),
                    icon=QtWidgets.QSystemTrayIcon.MessageIcon.Critical,
                )
                return None
        else:
            instance = self._instance

        return instance

    def start(self) -> None:
        """Start the instance."""

        self._tray.state_update(TITLE, "Starting...", STATE_PENDING)

        self._instance = self._get_instance()
        if self._instance is None:
            return

        if self._instance.is_running:
            self._tray.state_update(TITLE, "Already running", STATE_RUNNING)
            return

        def _start_wrapper() -> None:
            if self._instance is None:
                return

            try:
                self._instance.start()
            except SystemExit as error:
                self._instance = None
                self._tray.state_update(
                    TITLE,
                    "Failed to start",
                    STATE_ERROR.format(code=ExitCodes.get_name(error.code)),
                    icon=QtWidgets.QSystemTrayIcon.MessageIcon.Critical,
                )

        self._tray.state_update(TITLE, "Started", STATE_RUNNING)
        threading.Thread(target=_start_wrapper).start()

    def stop(self, before_quit: bool = False) -> None:
        """Stop the instance."""

        if self._instance is None:
            return

        self._instance.stop()
        self._instance = None
        if not before_quit:
            self._tray.state_update(
                TITLE,
                "Stopped",
                STATE_STOPPED,
                icon=QtWidgets.QSystemTrayIcon.MessageIcon.Warning,
            )

    def check_for_updates(self, auto: bool = False) -> None:
        """Check for updates."""

        if check_for_updates(
            "https://raw.github.com/erdoganonal/security-bypass/main",
            ".updater.hashes",
            self._args[1].updater_callback,
            max_retries=5,
            report_error=False,
            force_check=not auto,
        ):
            self.quit_application()
            complete_update()
        elif not auto:
            self._tray.state_update(TITLE, "No updates available")

    def open_password_manager(self) -> None:
        """Open the password manager."""
        # pylint: disable=consider-using-with
        subprocess.Popen([sys.executable, "password_manager.py"])

    def quit_application(self) -> None:
        """Stop the instance and quit the application"""

        self.stop(before_quit=True)

        self._tray.state_update(TITLE, "Exiting...", STATE_STOPPED)
        QtWidgets.QApplication.quit()


def main() -> None:
    """Start the tray application."""
    tray_app = SecurityBypassTray()
    sys.exit(tray_app.app.exec())


if __name__ == "__main__":
    main()

"""tray version of the security bypass application"""

# pylint: disable=c-extension-no-member

import subprocess
import sys
import threading
import time
from typing import Callable, Tuple

from PyQt6 import QtGui, QtWidgets

from common import exceptions
from common.tools import complete_update, is_interactive_authentication, restart_as_admin
from handlers.authentication.base import AuthenticationController
from handlers.notification.base import NotificationController
from handlers.notification.toast import NotificationToast
from handlers.window_selector.base import WindowSelectorController
from handlers.window_selector.pyqt_gui import WindowSelectorPyQtGUI
from helpers.user_preferences import UserPreferencesAccessor
from logger import initialize as logger_initialize
from logger import logger
from package_builder.registry import PBId, PBRegistry
from security_bypass import SecurityBypass
from settings import SECURITY_BYPASS_ICON, USER_PREFERENCES_FILE
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
        self.app.setStyle("windowsvista")
        self.app.setApplicationName(TITLE)
        self.app.setApplicationDisplayName(TITLE)
        self.app.setOrganizationName(TITLE)

        self.tray_icon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(str(SECURITY_BYPASS_ICON)), self.app)
        self.menu = QtWidgets.QMenu()

        self._action_manager = ActionManager(self)

        self.tray_icon.setContextMenu(self.menu)
        self.tray_icon.setToolTip(f"{TITLE} - Stopped")
        self.tray_icon.show()

    def add_actions(self) -> None:
        """Add the actions to the menu."""

        user_preferences = UserPreferencesAccessor.get()

        self.add_action(("Start", self._action_manager.start, None))
        self.add_action(("Stop", self._action_manager.stop, None))
        self.add_action(("Status", lambda: None, None))
        self.add_action(("Auto start on startup", self._action_manager.toggle_auto_start, user_preferences.auto_start))
        self.add_action(None)
        self.add_action(("Check for updates", self._action_manager.check_for_updates, None))
        self.add_action(("Check updates on startup", self._action_manager.toggle_check_for_updates, user_preferences.auto_update))
        self.add_action(None)
        self.add_action(("Password Manager", self._action_manager.open_password_manager, None))
        self.add_action(
            ("Repeated Window Protection", self._action_manager.set_repeated_window_protection, user_preferences.repeated_window_protection)
        )
        self.add_action(None)
        self.add_action(("Quit", self._action_manager.quit_application, None))

        if user_preferences.auto_update:
            self._action_manager.check_for_updates(auto=True)

        if user_preferences.auto_start:
            self._action_manager.start(delay_secs=30)
        else:
            logger.info("Auto start is disabled")
            self.tray_icon.setToolTip(STATE_READY)

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


class ActionManager:
    """Manage the actions for the tray icon."""

    def __init__(self, tray: SecurityBypassTray) -> None:
        self._security_bypass = SecurityBypass()
        self._tray = tray
        self._exit_in_progress = False

    def toggle_auto_start(self, checked: bool) -> None:
        """Toggle the check for updates feature."""
        UserPreferencesAccessor.partial_save(USER_PREFERENCES_FILE, auto_start=checked)

    def toggle_check_for_updates(self, checked: bool) -> None:
        """Toggle the check for updates feature."""
        UserPreferencesAccessor.partial_save(USER_PREFERENCES_FILE, auto_update=checked)

    def set_repeated_window_protection(self, checked: bool) -> None:
        """Toggle the repeated window protection feature."""
        UserPreferencesAccessor.partial_save(USER_PREFERENCES_FILE, repeated_window_protection=checked)

    def set_status_text(self, text: str) -> None:
        """Set the status text."""

        try:
            status_action = next(filter(lambda action: action.text().startswith("Status"), self._tray.menu.actions()))
            status_action.setText(f"Status: {text}")
        except StopIteration:
            pass

    def start(self, delay_secs: int = 0) -> None:
        """Start the instance."""

        notification_controller = PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController)
        notification_controller.debug("Starting...")

        if self._security_bypass.is_running:
            notification_controller.error("Already running")
            return

        self._tray.tray_icon.setToolTip(STATE_PENDING)

        def _start_wrapper() -> None:
            for _ in range(delay_secs):
                if self._exit_in_progress:
                    logger.warning("Exit in progress, not starting the security bypass")
                    return

                time.sleep(1)

            self.set_status_text("Running")
            self._tray.tray_icon.setToolTip(STATE_RUNNING)

            try:
                self._security_bypass.start()
            except exceptions.ToolError as error:
                notification_controller.error(error.message)
                self._tray.tray_icon.setToolTip(STATE_ERROR.format(code=error.get_error_code))
                self.set_status_text(f"Error({error.title})")
            except Exception as error:  # pylint: disable=broad-exception-caught
                logger.error("Error starting the security bypass: %s", error)
                self.set_status_text("Unknown Error: Please check the logs")

        threading.Thread(target=_start_wrapper).start()

    def stop(self, before_quit: bool = False) -> None:
        """Stop the instance."""

        self._security_bypass.stop(before_quit=before_quit)
        if not before_quit:
            self._tray.tray_icon.setToolTip(STATE_STOPPED)

        self.set_status_text("Stopped")

    def check_for_updates(self, auto: bool = False) -> None:
        """Check for updates."""

        has_updates = check_for_updates(report_error=False, force_check=not auto)

        if has_updates:
            self.quit_application()
            complete_update()

    def open_password_manager(self) -> None:
        """Open the password manager."""
        # pylint: disable=consider-using-with
        subprocess.Popen([sys.executable, "password_manager.py"])

    def quit_application(self) -> None:
        """Stop the instance and quit the application"""

        self._exit_in_progress = True
        self.stop(before_quit=True)

        PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController).warning("Exiting...")
        QtWidgets.QApplication.quit()


def main() -> None:
    """Start the tray application."""
    logger_initialize()

    user_preferences = UserPreferencesAccessor.get()
    if user_preferences.auth_method.is_admin_rights_required and is_interactive_authentication():
        restart_as_admin()

    # create the instance here to have the tray icon available
    tray_app = SecurityBypassTray()

    PBRegistry.register_safe(PBId.NOTIFICATION_HANDLER, NotificationController(NotificationToast()))
    PBRegistry.register_safe(PBId.SELECT_WINDOW, WindowSelectorController(WindowSelectorPyQtGUI()))
    PBRegistry.register_safe(PBId.AUTHENTICATION_HANDLER, AuthenticationController(user_preferences.auth_method))

    PBRegistry.check_all_registered()

    tray_app.add_actions()
    sys.exit(tray_app.app.exec())


if __name__ == "__main__":
    main()

"""This module contains the ImportConfigDialog class"""

# pylint: disable=c-extension-no-member

import sys
from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtWidgets

from common.tools import is_user_admin, restart_as_admin
from config.config import ConfigManager
from handlers.authentication import face_recognition, fingerprint
from handlers.authentication.methods import AuthMethod
from helpers.ui_helpers.constants import TITLE_PASSWORD_MANAGER as TITLE
from helpers.ui_helpers.notification import Notification
from helpers.ui_helpers.pm.dialogs.auth_method import AuthMethodDialog
from helpers.ui_helpers.pm.dialogs.import_config import ImportConfigDialog
from helpers.ui_helpers.pm.dialogs.password import PasswordDialog
from helpers.user_preferences import UserPreferencesAccessor
from logger import logger
from settings import ABOUT_INFO, ABOUT_MESSAGE, CREDENTIALS_FILE, USER_PREFERENCES_FILE, VERSION

if TYPE_CHECKING:
    from password_manager import PasswordManagerUI

CLI_ARG_AUTH_METHOD = "--auth-method"


class MenuActionHandler:
    """handle the menu actions"""

    def __init__(self, manager: "PasswordManagerUI") -> None:
        self._manager = manager

    def import_config(self) -> None:
        """import the configuration from a file"""

        result = ImportConfigDialog().get()
        if result is None:
            return

        master_key, config = result

        ConfigManager(master_key).save_config(config)
        self._manager.rerender(master_key, config)

        Notification.show_info(self._manager.ui.tree, "The configuration imported successfully", "Import Successful")

    def export_config(self) -> None:
        """export the configuration to a file"""
        file, _ = QtWidgets.QFileDialog.getSaveFileName(
            self._manager.ui.tree,
            "Export Configuration",
            "",
            "Credentials Files (*.credentials)",
        )

        if not file:
            return

        save_encrypted = Notification.ask_yes_no(
            self._manager.ui.tree,
            message="Do you want to save the data in encrypted format?",
            title="Encryption Preference",
            info="Warning: If you export without encryption, the credentials will be visible easily. "
            "Otherwise, the master key will be required to import it.",
        )

        if save_encrypted:
            with open(CREDENTIALS_FILE, "rb") as credentials_fd:
                data = credentials_fd.read()
        else:
            data = self._manager.get_config().to_json(encode=True)

        with open(file, "wb") as out_file_fd:
            out_file_fd.write(data)

        Notification.show_info(self._manager.ui.tree, "The configuration exported successfully", "Export Successful")

    def _handle_admin_request(self, auth_method: AuthMethod) -> None:
        """Ask user to restart the application"""
        if Notification.ask_yes_no(
            self._manager.ui.tree,
            f"Admin privileges are required to read the {auth_method.value}.",
            "Admin Privileges Required",
            info="Do you want to restart the application?",
        ):
            if qt_instance := QtWidgets.QApplication.instance():
                qt_instance.quit()
            restart_as_admin(f"{CLI_ARG_AUTH_METHOD} {auth_method.value}")

    def change_master_key_dialog(self, auth_method: AuthMethod | None = None) -> None:
        """open a dialog window and ask user to enter a new master key"""

        auth_method = auth_method or UserPreferencesAccessor.get().auth_method

        password: str | None = None
        if auth_method is not None:
            if auth_method.is_admin_rights_required and not is_user_admin():
                self._handle_admin_request(auth_method)

            result = auth_method.get_auth_result()
            if result["error_code"] != 0:
                Notification.show_error(
                    self._manager.ui.tree,
                    result["error"],
                    f"{auth_method.value} Error",
                    info=f"Error Code: {result['error_code']}",
                )
                return
            password = result["hash"]

        if password is None:
            return

        UserPreferencesAccessor.partial_save(USER_PREFERENCES_FILE, auth_method=auth_method)

        if self._manager.change_master_key(password):
            Notification.show_info(self._manager.ui.tree, "The master key changed successfully", "Master Key Changed")
        else:
            Notification.show_warning(
                self._manager.ui.tree,
                "The master key changed successfully",
                "Master Key Changed",
                info="But, failed to inform the SecurityBypass.\n"
                "Please check if the SecurityBypass is running.\n"
                "A restart may be required to apply the changes.",
            )

    def change_auth_method_dialog(self, current_method: str | None = None) -> None:
        """Change the authentication method"""

        auth_method = AuthMethodDialog(current_method).get()
        if auth_method is None:
            return

        self.change_master_key_dialog(auth_method)

    def show_version(self) -> None:
        """show the version of the application"""
        Notification.show_info(self._manager.ui.tree, f"{TITLE}\n\nVersion: {VERSION}", TITLE + " - Version")

    def show_about(self) -> None:
        """show the about message"""
        Notification.show_info(self._manager.ui.tree, ABOUT_MESSAGE, TITLE, info=ABOUT_INFO)

    def connect(self) -> None:
        """connect the menu actions to the functions"""

        # Configurations
        self._manager.ui.action_import.triggered.connect(self.import_config)
        self._manager.ui.action_export.triggered.connect(self.export_config)
        # Settings
        self._manager.ui.action_change_master_key.triggered.connect(self.change_master_key_dialog)
        self._manager.ui.action_change_auth_method.triggered.connect(self.change_auth_method_dialog)
        # Help
        self._manager.ui.action_version.triggered.connect(self.show_version)
        self._manager.ui.action_about.triggered.connect(self.show_about)

        self._bind_auth_method_change_request_after_restart()

    def _bind_auth_method_change_request_after_restart(self) -> None:
        """Bind the authentication method change request after restart"""

        try:
            auth_method_index = sys.argv.index(CLI_ARG_AUTH_METHOD)
        except ValueError:
            return

        try:
            auth_method = AuthMethod(sys.argv[auth_method_index + 1])
        except (ValueError, IndexError) as error:
            logger.critical("Invalid authentication method: %s", error)
            return

        open_change_auth_method_dialog_timer = QtCore.QTimer(QtWidgets.QApplication.instance())
        open_change_auth_method_dialog_timer.setSingleShot(True)
        open_change_auth_method_dialog_timer.timeout.connect(lambda: self.change_master_key_dialog(auth_method))
        open_change_auth_method_dialog_timer.start(100)

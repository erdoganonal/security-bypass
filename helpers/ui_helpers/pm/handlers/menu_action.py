"""This module contains the ImportConfigDialog class"""

# pylint: disable=c-extension-no-member

from typing import TYPE_CHECKING

from PyQt6 import QtWidgets

from authentication import fingerprint
from authentication.methods import AuthMethod
from config.config import ConfigManager
from helpers.config_manager import ConfigManager as ToolConfigManager
from helpers.ui_helpers.constants import TITLE_PASSWORD_MANAGER as TITLE
from helpers.ui_helpers.notification import Notification
from helpers.ui_helpers.pm.dialogs.auth_method import AuthMethodDialog
from helpers.ui_helpers.pm.dialogs.import_config import ImportConfigDialog
from helpers.ui_helpers.pm.dialogs.password import PasswordDialog
from settings import ABOUT_INFO, ABOUT_MESSAGE, CREDENTIALS_FILE, TOOL_CONFIG_FILE, VERSION

if TYPE_CHECKING:
    from password_manager import PasswordManagerUI


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

    def change_master_key_dialog(self, auth_method: AuthMethod | None = None) -> None:
        """open a dialog window and ask user to enter a new master key"""

        auth_method = auth_method or ToolConfigManager.get_config().auth_method

        password: str | None = None
        if auth_method == AuthMethod.PASSWORD:
            password = PasswordDialog().get()
        elif auth_method == AuthMethod.FINGERPRINT:
            if not Notification.ask_yes_no(
                self._manager.ui.tree,
                "Admin privileges are required to read the fingerprint.",
                "Admin Privileges Required",
                info="Do you want to continue?",
            ):
                self.change_auth_method_dialog(auth_method.value)
                return
            result = fingerprint.get_fingerprint_result()
            if result["error_code"] != 0:
                Notification.show_error(
                    self._manager.ui.tree,
                    result["error"],
                    "Fingerprint Error",
                    info=f"Error Code: {result['error_code']}",
                )
                return
            password = result["hash"]
        else:
            raise ValueError(f"Unknown auth method: {auth_method}")

        if password is None:
            return

        ToolConfigManager.partial_save(TOOL_CONFIG_FILE, auth_method=auth_method)

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

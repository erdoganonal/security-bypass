"""This module contains the ImportConfigDialog class"""

# pylint: disable=c-extension-no-member

import json
from pathlib import Path
from typing import Tuple, Type

from PyQt6 import QtCore, QtWidgets

from common.password_validator import PASSWORD_SCHEMA, get_password_hint
from config.config import Config, ConfigManager
from generated.ui_generated_import_config_dialog import Ui_ImportConfigDialog  # type: ignore[attr-defined]
from helpers.ui_helpers.notification import Notification
from helpers.ui_helpers.pm.dialogs.dialog_base import DialogBase, SupportsSetupUi
from settings import DFT_ENCODING

_QT_STATE_CHECKED: int = QtCore.Qt.CheckState.Checked.value  # type: ignore[assignment]
_QT_STATE_UNCHECKED: int = QtCore.Qt.CheckState.Unchecked.value  # type: ignore[assignment]


class ImportConfigDialog(DialogBase[Tuple[bytes, Config], Ui_ImportConfigDialog]):
    """opens a dialog and waits for user input"""

    @property
    def skeleton(self) -> Type[SupportsSetupUi]:
        return Ui_ImportConfigDialog  # type: ignore[no-any-return]

    def _is_valid_file(self, file: str) -> bool:
        if not file:
            Notification.show_error(self._wrapper_widget, "The file path cannot be empty", "Empty File Path")
        elif not Path(file).exists():
            Notification.show_error(self._wrapper_widget, "The file does not exist", "File Not Found")
        else:
            return True
        return False

    def _is_valid_master_key(self, master_key: str, verify: bool) -> bool:
        if not master_key:
            Notification.show_error(self._wrapper_widget, "The master key cannot be empty", "Empty Master Key")
        elif verify and master_key != self._ui.entry_master_key_again.text():
            Notification.show_error(self._wrapper_widget, "the master keys did not match", "Master Key did not match")
        elif not PASSWORD_SCHEMA.validate(master_key):
            Notification.show_error(
                self._wrapper_widget,
                "The master key did not met the requirements\n\n" + get_password_hint(70),
                "Master Key did not met the requirements",
            )
        else:
            return True
        return False

    def accept(self) -> None:
        """this function is called when OK button is pressed"""
        file_master_key = ""
        master_key = ""
        file = self._ui.entry_config_file.text()

        if not self._is_valid_file(file):
            return

        is_encrypted_file = self._ui.checkbox_is_encrypted_file.isChecked()
        use_same_master_key = self._ui.checkbox_use_same_master_key.isChecked()
        file_master_key = self._ui.entry_file_master_key.text()

        if is_encrypted_file and use_same_master_key:
            master_key = file_master_key
        else:
            master_key = self._ui.entry_master_key.text()

        if not self._is_valid_master_key(master_key, not use_same_master_key):
            return

        with open(file, "rb") as file_fd:
            data = file_fd.read()

        if is_encrypted_file:
            try:
                data = ConfigManager(file_master_key.encode(DFT_ENCODING)).decrypt(data)
            except ValueError:
                Notification.show_error(
                    self._wrapper_widget, "The master key is wrong or file format is invalid", "Wrong Master Key or Invalid File Format"
                )
                return

        try:
            self._data = (master_key.encode(DFT_ENCODING), Config.from_json(data))
        except json.JSONDecodeError:
            Notification.show_error(
                self._wrapper_widget, "The file is not a valid credential file", "Invalid File", info="Is it encrypted?"
            )
            return

        self.close()

    def _browse(self) -> None:
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self._wrapper_widget,
            "Select the credential file",
            "",
            "Credentials Files (*.credentials)",
            options=QtWidgets.QFileDialog.Option.ReadOnly,
        )
        if not file_path:
            return

        self._ui.entry_config_file.setText(file_path)

    def _toggle_encryption(self, state: int) -> None:
        enabled = state == _QT_STATE_CHECKED

        self._ui.label_file_master_key.setEnabled(enabled)
        self._ui.entry_file_master_key.setEnabled(enabled)
        self._ui.checkbox_use_same_master_key.setEnabled(enabled)

        self._toggle_master_key_entry(
            _QT_STATE_CHECKED if self._ui.checkbox_use_same_master_key.isChecked() and enabled else _QT_STATE_UNCHECKED
        )

    def _toggle_master_key_entry(self, state: int) -> None:
        disabled = state != _QT_STATE_CHECKED

        self._ui.label_master_key.setEnabled(disabled)
        self._ui.entry_master_key.setEnabled(disabled)
        self._ui.label_master_key_again.setEnabled(disabled)
        self._ui.entry_master_key_again.setEnabled(disabled)

    def configure(self) -> None:
        self._ui.button_browse.clicked.connect(self._browse)

        self._ui.checkbox_is_encrypted_file.stateChanged.connect(self._toggle_encryption)
        self._ui.checkbox_use_same_master_key.stateChanged.connect(self._toggle_master_key_entry)

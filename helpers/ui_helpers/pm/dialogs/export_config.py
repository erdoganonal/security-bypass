"""This module contains the ExportConfigDialog class"""

# pylint: disable=c-extension-no-member

from dataclasses import dataclass
from pathlib import Path
from typing import Type

from PyQt6 import QtWidgets

from generated.ui_generated_export_config_dialog import Ui_ExportConfigDialog  # type: ignore[attr-defined]
from helpers.ui_helpers.notification import Notification
from helpers.ui_helpers.pm.dialogs.dialog_base import QT_STATE_CHECKED, DialogBase, SupportsSetupUi


@dataclass
class ExportConfigResult:
    """the result of the export config dialog"""

    path: Path
    need_save_encrypted: bool
    use_same_master_key: bool
    master_key: str = ""  # only used when need_save_encrypted is True and use_same_master_key is False


class ExportConfigDialog(DialogBase[ExportConfigResult, Ui_ExportConfigDialog]):
    """opens a dialog and waits for user input"""

    @property
    def skeleton(self) -> Type[SupportsSetupUi]:
        return Ui_ExportConfigDialog  # type: ignore[no-any-return]

    def _browse(self) -> None:
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self._wrapper_widget,
            "Select the location to save the file",
            "",
            "Credentials Files (*.credentials)",
            options=QtWidgets.QFileDialog.Option.ReadOnly,
        )
        if not file_path:
            return

        self._ui.entry_export_location.setText(file_path)

    def _is_valid_file(self, file: str) -> bool:
        if not file:
            Notification.show_error(self._wrapper_widget, "The file path cannot be empty", "Empty File Path")
        elif not Path(file).parent.exists():
            Notification.show_error(self._wrapper_widget, "The directory does not exist", "Invalid Directory")
        else:
            return True
        return False

    def accept(self) -> None:
        """this function is called when OK button is pressed"""

        path = self._ui.entry_export_location.text()
        if not self._is_valid_file(path):
            return

        need_save_encrypted = self._ui.checkbox_need_save_encrypted.isChecked()
        use_same_master_key = self._ui.checkbox_use_same_master_key.isChecked()

        new_master_key = self._ui.entry_master_key.text()
        new_master_key_again = self._ui.entry_master_key_again.text()
        if need_save_encrypted and not use_same_master_key and not self._is_valid_master_key(new_master_key, new_master_key_again):
            return

        self._data = ExportConfigResult(
            path=Path(path),
            need_save_encrypted=need_save_encrypted,
            use_same_master_key=use_same_master_key,
            master_key=new_master_key,
        )

        self.close()

    def _toggle_encryption(self, state: int) -> None:
        enabled = state == QT_STATE_CHECKED
        self._ui.checkbox_use_same_master_key.setEnabled(enabled)

        if enabled and self._ui.checkbox_use_same_master_key.isChecked():
            return

        self._ui.label_master_key.setEnabled(enabled)
        self._ui.entry_master_key.setEnabled(enabled)
        self._ui.label_master_key_again.setEnabled(enabled)
        self._ui.entry_master_key_again.setEnabled(enabled)

    def _toggle_master_key_entry(self, state: int) -> None:
        disabled = state != QT_STATE_CHECKED

        self._ui.label_master_key.setEnabled(disabled)
        self._ui.label_master_key_again.setEnabled(disabled)
        self._ui.entry_master_key.setEnabled(disabled)
        self._ui.entry_master_key_again.setEnabled(disabled)

    def configure(self) -> None:
        self._ui.button_browse.clicked.connect(self._browse)
        self._ui.checkbox_need_save_encrypted.stateChanged.connect(self._toggle_encryption)
        self._ui.checkbox_use_same_master_key.stateChanged.connect(self._toggle_master_key_entry)

        self._ui.checkbox_need_save_encrypted.setChecked(True)
        self._ui.checkbox_use_same_master_key.setChecked(True)

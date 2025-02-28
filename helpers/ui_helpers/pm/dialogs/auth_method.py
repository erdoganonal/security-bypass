"""This module contains the AuthMethodDialog class"""

# pylint: disable=c-extension-no-member

from typing import Type

from authentication.methods import AuthMethod
from generated.ui_generated_auth_method_dialog import Ui_GetAuthMethodDialog  # type: ignore[attr-defined]
from helpers.config_manager import ConfigManager
from helpers.ui_helpers.pm.dialogs.dialog_base import DialogBase, SupportsSetupUi
from settings import TOOL_CONFIG_FILE


class AuthMethodDialog(DialogBase[AuthMethod, Ui_GetAuthMethodDialog]):
    """opens a dialog and waits for user input"""

    def __init__(self, current_method_name: str | None = None) -> None:
        super().__init__()
        self._current_method_name = current_method_name or ConfigManager.get_config().auth_method.value

    @property
    def skeleton(self) -> Type[SupportsSetupUi]:
        return Ui_GetAuthMethodDialog  # type: ignore[no-any-return]

    def accept(self) -> None:
        """this function is called when OK button is pressed"""

        self._data = AuthMethod.PASSWORD
        current_text = self._ui.comboBox.currentText()

        for method in AuthMethod:
            if method.value == current_text:
                self._data = method
                break

        if self._data == ConfigManager.get_config().auth_method:
            self._data = None

        self.close()

    def configure(self) -> None:
        for method in AuthMethod:
            self._ui.comboBox.addItem(method.value)

        self._ui.comboBox.setCurrentText(self._current_method_name)

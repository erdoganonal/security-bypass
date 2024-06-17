"""This module contains the PasswordDialog class"""

# pylint: disable=c-extension-no-member

from typing import Type

from common.password_validator import PASSWORD_SCHEMA, get_password_hint
from generated.ui_generated_get_password_dialog import Ui_GetPasswordDialog  # type: ignore[attr-defined]
from helpers.ui_helpers.notification import Notification
from helpers.ui_helpers.pm.dialogs.dialog_base import DialogBase, SupportsSetupUi


class PasswordDialog(DialogBase[str, Ui_GetPasswordDialog]):
    """opens a dialog and waits for user input"""

    @property
    def skeleton(self) -> Type[SupportsSetupUi]:
        return Ui_GetPasswordDialog  # type: ignore[no-any-return]

    def accept(self) -> None:
        """this function is called when OK button is pressed"""

        password = self._ui.entry_password.text()
        password_again = self._ui.entry_password_again.text()

        if not password:
            Notification.show_error(self._wrapper_widget, "The password cannot be empty", "Empty Password")
        elif password != password_again:
            Notification.show_error(self._wrapper_widget, "The passwords did not match", "Password did not match")
        elif PASSWORD_SCHEMA.validate(password):
            self._data = password
            self.close()
        else:
            Notification.show_error(
                self._wrapper_widget,
                "The passwords did not met the requirements",
                "Password did not met the requirements",
            )

    def configure(self) -> None:
        self._ui.label_password_hint.setText(get_password_hint(70))

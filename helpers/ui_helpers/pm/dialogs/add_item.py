"""This module contains the AddItemDialog class"""

# pylint: disable=c-extension-no-member

from typing import List, Type, TypedDict

from PyQt6 import QtCore, QtGui, QtWidgets

from generated.ui_generated_add_item_dialog import Ui_AddItemDialog  # type: ignore[attr-defined]
from helpers.ui_helpers.notification import Notification
from helpers.ui_helpers.pm.dialogs.dialog_base import DialogBase


class AddItemDialog(DialogBase["AddItemDialog.Data", Ui_AddItemDialog]):
    """a dialog widget to get user input for adding a new item"""

    class Data(TypedDict):
        """the return data of AddItemDialog"""

        group: str | None
        name: str
        title: str
        send_enter: bool

    def __init__(self, groups: List[str], selected: str | None = None) -> None:
        self._groups = groups
        self._selected = selected
        super().__init__()

    @property
    def skeleton(self) -> Type[Ui_AddItemDialog]:
        return Ui_AddItemDialog  # type: ignore[no-any-return]

    def setup(self) -> None:
        """setup the dialog"""

        self._wrapper_widget.setWindowTitle("Add New Item")

        self._ui.dropdown_group.addItem("No group")
        self._ui.dropdown_group.addItems(self._groups)
        self._ui.dropdown_group.addItem("Create new...")

        italic_font = QtGui.QFont("Times", italic=True)
        self._ui.dropdown_group.setItemData(0, italic_font, QtCore.Qt.ItemDataRole.FontRole)
        self._ui.dropdown_group.setItemData(len(self._groups) + 1, italic_font, QtCore.Qt.ItemDataRole.FontRole)

    def get(self) -> Data | None:
        """show the add item dialog and return the data if OK clicked."""

        self.setup()
        index = self._ui.dropdown_group.findText(self._selected)
        if index != -1:
            self._ui.dropdown_group.setCurrentIndex(index)

        return super().get()

    def _get_new_group_name(self) -> str | None:
        group, ok = QtWidgets.QInputDialog.getText(self._wrapper_widget, "New Group Name", "Enter the new group name:")
        if not ok:
            return None

        index = self._ui.dropdown_group.findText(group)
        if index == -1:
            return group

        Notification.show_error(self._wrapper_widget, "The group name is already exists.", "The Group Already Exists")
        self._ui.dropdown_group.setCurrentIndex(index)

        return None

    def accept(self) -> None:
        current_index = self._ui.dropdown_group.currentIndex()
        if current_index == 0:
            group = None
        elif current_index == len(self._groups) + 1:
            group = self._get_new_group_name()
            if group is None:
                return
        else:
            group = self._ui.dropdown_group.currentText()

        title = self._ui.entry_title.text()
        name = self._ui.entry_name.text()
        for value, value_str in ((title, "title"), (name, "name")):
            if not value:
                Notification.show_error(self._wrapper_widget, f"The {value_str} cannot left empty", f"Empty {value_str}".title())
                return

        self._data = AddItemDialog.Data(group=group, name=name, title=title, send_enter=True)

        self.close()

"""SignalHandler"""

# pylint: disable=c-extension-no-member


from typing import TYPE_CHECKING

from PyQt6 import QtCore, QtWidgets

from config.config import WindowData
from helpers.ui_helpers.altered import QStandardPasskeyItem
from helpers.ui_helpers.notification import Notification
from helpers.ui_helpers.pm.dialogs.add_item import AddItemDialog
from helpers.ui_helpers.pm.focus_map import FocusMap
from helpers.ui_helpers.pm.handlers.menu_action import MenuActionHandler

if TYPE_CHECKING:
    from password_manager import PasswordManagerUI


class SignalHandler:
    """signal handlers"""

    def __init__(self, manager: "PasswordManagerUI") -> None:
        self._manager = manager
        self._old_item: QStandardPasskeyItem | None = None

        self._focus_map = FocusMap()
        self._menu_action_handler = MenuActionHandler(self._manager)

    def get_current_item(self, index: QtCore.QModelIndex | None = None) -> QStandardPasskeyItem:
        """return the window config for given index"""

        if index is None:
            try:
                index = self._manager.ui.tree.selectedIndexes()[0]
            except IndexError as err:
                raise ValueError("no item is selected") from err

        item = self._manager.model.itemFromIndex(index)
        if item is None:
            raise ValueError("cannot retrieve the current item")
        if isinstance(item, QStandardPasskeyItem):
            return item
        raise TypeError("The item type is not QStandardPasskeyItem")

    def toggle_password(self) -> None:
        """when the show password checkbutton clicked, show/hide the password"""

        if self._manager.ui.checkbox_toggle_password.isChecked():
            self._manager.ui.entry_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Normal)
        else:
            self._manager.ui.entry_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)

    def set_controller_visibility(self, index: QtCore.QModelIndex) -> None:
        """change the visibility of the add/remove buttons"""

        parent = index.parent().data()
        current = index.data()

        self._manager.ui.button_delete_item.setEnabled(bool(parent or current))

    def _get_first_unsaved(self) -> str | None:
        if self._old_item is None or self._old_item.window is None:
            return None

        item_compare_map = (
            ("title", self._old_item.window.title, self._manager.ui.entry_title.text()),
            ("name", self._old_item.window.name, self._manager.ui.entry_name.text()),
            ("auto_key_trigger", self._old_item.window.auto_key_trigger, self._manager.ui.entry_auto_key_trigger.text()),
            ("password", self._old_item.window.passkey, self._manager.ui.entry_password.text()),
            ("verify_sent", self._old_item.window.verify_sent, self._manager.ui.checkbox_toggle_verification.isChecked()),
        )

        for name, old_value, new_value in item_compare_map:
            if new_value != old_value:
                return name

        return None

    def load_window_config(self, index: QtCore.QModelIndex) -> None:
        """load the config widget based on selected item"""

        current_item = self.get_current_item(index)

        if self._old_item is current_item and current_item.text() == self._manager.ui.entry_name.text():
            # ignore the click if the item and it's title remained the same
            return

        unsaved = self._get_first_unsaved()
        if unsaved is not None and self._old_item is not current_item:
            question = QtWidgets.QMessageBox.question(
                self._manager.ui.tree, "Are you sure?", f"The {unsaved} has been changed and not saved. Are you sure to discard?"
            )
            if question != QtWidgets.QMessageBox.StandardButton.Yes:
                self._manager.ui.tree.setCurrentIndex(self._manager.model.indexFromItem(self._old_item))
                return

        self._old_item = current_item
        window = current_item.window

        items = (
            (self._manager.ui.entry_title, True),
            (self._manager.ui.entry_name, True),
            (self._manager.ui.entry_auto_key_trigger, True),
            (self._manager.ui.entry_password, True),
            (self._manager.ui.checkbox_toggle_password, False),
            (self._manager.ui.checkbox_toggle_verification, False),
            (self._manager.ui.button_save, False),
        )

        if window is None:
            for item, set_text in items:
                item.setDisabled(True)
                if set_text:
                    item.setText("")
            return

        for item, _ in items:
            item.setDisabled(False)

        self._manager.ui.entry_title.setText(window.title)
        self._manager.ui.entry_name.setText(window.name)
        self._manager.ui.entry_auto_key_trigger.setText(window.auto_key_trigger)
        self._manager.ui.entry_password.setText(window.passkey)
        self._manager.ui.checkbox_toggle_verification.setChecked(window.verify_sent)

    def add_item_dialog(self) -> None:
        """open a dialog window and get the necessary data for a new item"""

        root = self._manager.model.invisibleRootItem()
        if root is None:
            return

        groups = []
        for row in range(root.rowCount()):
            child = root.child(row)
            if child and isinstance(child, QStandardPasskeyItem) and child.window is None:
                groups.append(child.text())

        try:
            item = self.get_current_item()
            parent = item.parent()
            if parent is None:
                selected_group = item.text() if item.window is None else None
            else:
                selected_group = parent.text()
        except ValueError:
            selected_group = None

        data = AddItemDialog(groups, selected_group).get()
        if data is not None:
            self._manager.add_item(WindowData(**data, auto_key_trigger="", passkey=""))

    def delete_item(self) -> None:
        """delete the selected item from the tree"""
        current_item = self.get_current_item()

        self._manager.remove_item(current_item)

    def save_item(self) -> None:
        """save all configuration for given item"""

        title = self._manager.ui.entry_title.text()
        name = self._manager.ui.entry_name.text()
        auto_key_trigger = self._manager.ui.entry_auto_key_trigger.text()
        passkey = self._manager.ui.entry_password.text()

        for value, value_str in ((title, "title"), (name, "name")):
            if not value:
                Notification.show_error(self._manager.ui.tree, f"The {value_str} cannot left empty", f"Empty {value_str}".title())
                return

        window = self.get_current_item().window
        if window:
            window.title = title
            window.name = name
            window.auto_key_trigger = auto_key_trigger
            window.passkey = passkey
            window.verify_sent = self._manager.ui.checkbox_toggle_verification.isChecked()

            self._manager.update_window()

        self._item_changed()

    def _item_changed(self) -> None:
        self._manager.ui.button_save.setEnabled(self._get_first_unsaved() is not None)

    def bind(self) -> None:
        """bind signals"""

        self._focus_map.add(
            self._manager.ui.entry_title,
            self._manager.ui.entry_name,
            self._manager.ui.entry_auto_key_trigger,
            self._manager.ui.entry_password,
            self._manager.ui.checkbox_toggle_password,
            self._manager.ui.checkbox_toggle_verification,
            self._manager.ui.button_save,
        )
        self._focus_map.bind(self._manager.ui.frame)

        self._manager.ui.checkbox_toggle_password.stateChanged.connect(self.toggle_password)
        self._manager.ui.tree.clicked.connect(self.set_controller_visibility)
        self._manager.ui.tree.clicked.connect(self.load_window_config)

        self._manager.ui.button_add_item.clicked.connect(self.add_item_dialog)
        self._manager.ui.button_delete_item.clicked.connect(self.delete_item)

        self._manager.ui.entry_title.textChanged.connect(lambda _: self._item_changed())
        self._manager.ui.entry_auto_key_trigger.textChanged.connect(lambda _: self._item_changed())
        self._manager.ui.entry_name.textChanged.connect(lambda _: self._item_changed())
        self._manager.ui.entry_password.textChanged.connect(lambda _: self._item_changed())
        self._manager.ui.checkbox_toggle_verification.stateChanged.connect(lambda _: self._item_changed())

        self._manager.ui.button_save.clicked.connect(self.save_item)

        self._menu_action_handler.connect()

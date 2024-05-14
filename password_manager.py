"""a UI to manage the passwords"""

# pylint: disable=c-extension-no-member

import sys
from typing import Any, List, TypedDict

from PyQt6 import QtCore, QtGui, QtWidgets

from common.exit_codes import ExitCodes
from config.config import Config, ConfigManager, WindowConfig
from config.config_key_manager import check_config_file, validate_and_get_mk
from generated.ui_generated_add_item_dialog import Ui_AddItemWidget  # type: ignore[attr-defined]
from generated.ui_generated_main import Ui_MainWindow  # type: ignore[attr-defined]
from notification_handler.gui import GUINotificationHandler


# pylint: disable=too-few-public-methods
class QStandardPasskeyItem(QtGui.QStandardItem):
    """customized q-item for window config"""

    def __init__(self, text: str, window: WindowConfig | None) -> None:
        super().__init__(text)
        self.window = window

    @classmethod
    def clone_from(cls, item: "QStandardPasskeyItem") -> "QStandardPasskeyItem":
        """clone a QStandardPasskeyItem and return as a new item"""

        return cls(text=item.text(), window=item.window)


class Hooks:
    """allows to to customized actions on specific methods"""

    def __init__(self, manager: "PasswordManagerUI") -> None:
        self._manager = manager
        self.i = 0

    def drag_move_event_hook(self, event: QtGui.QDragMoveEvent) -> None:
        """event for drag and drop items."""

        current_item = self._manager.model.itemFromIndex(self._manager.ui.tree.currentIndex())

        target_item = self._manager.model.itemFromIndex(
            self._manager.ui.tree.indexAt(QtCore.QPoint(int(event.position().x()), int(event.position().y())))
        )
        if target_item and isinstance(target_item, QStandardPasskeyItem) and target_item.window is not None:
            event.ignore()
        elif current_item and isinstance(current_item, QStandardPasskeyItem) and current_item.window is None:
            event.ignore()
        else:
            QtWidgets.QTreeView.dragMoveEvent(self._manager.ui.tree, event)

    def drop_event_hook(self, event: QtGui.QDropEvent) -> None:
        """event for drag and drop items."""

        current_index = self._manager.ui.tree.currentIndex()
        current_item = self._manager.model.itemFromIndex(current_index)
        target_index = self._manager.ui.tree.indexAt(QtCore.QPoint(int(event.position().x()), int(event.position().y())))
        target_item = self._manager.model.itemFromIndex(target_index)

        if isinstance(current_item, QStandardPasskeyItem) and (isinstance(target_item, QStandardPasskeyItem) or target_item is None):
            self._manager.move_item(current_item, target_item)

    def hook(self) -> None:
        """replace the original methods with hooks"""

        self._manager.ui.tree.dragMoveEvent = self.drag_move_event_hook
        self._manager.ui.tree.dropEvent = self.drop_event_hook


class PasswordManagerUI:
    """a UI to manage the passwords"""

    def __init__(self) -> None:
        self._notification_handler = GUINotificationHandler()

        self._config_mgr: ConfigManager
        self._config: Config

        self._get_config_manager()

        self.model = QtGui.QStandardItemModel()
        setattr(self.model, "setData", self._set_data_hook)
        self.ui = Ui_MainWindow()

        self._handler = SignalHandler(self)

    def _set_data_hook(self, index: QtCore.QModelIndex, value: Any, role: int = 0) -> bool:
        old_value = None
        if role == QtCore.Qt.ItemDataRole.EditRole:
            old_value = index.data(QtCore.Qt.ItemDataRole.DisplayRole)

        res = QtGui.QStandardItemModel.setData(self.model, index, value, role)
        if not res:
            return res

        item: QStandardPasskeyItem | None = self.model.itemFromIndex(index)  # type: ignore[assignment]
        if item is None:
            return False

        if item.window is None:
            # parent item is changed, all group names should be updated
            self._config.update_group_name(old_value, value)  # type: ignore[arg-type]
        else:
            item.window.name = value

        self._config_mgr.save_config(self._config)
        self._refresh()

        return True

    def _refresh(self) -> None:
        self._handler.load_window_config(self.ui.tree.currentIndex())

    def _get_config_manager(self) -> None:
        try:
            check_config_file()

            self._config_mgr = ConfigManager(key=validate_and_get_mk())
            self._config = self._config_mgr.get_config()
        except ValueError:
            self._notification_handler.error("Cannot load configurations. The Master Key is wrong.")
            ExitCodes.WRONG_MASTER_KEY.exit()
        except KeyError as err:
            self._notification_handler.error(err.args[0])
            ExitCodes.EMPTY_MASTER_KEY.exit()
        except FileNotFoundError:
            # Initial usage, create an empty config file
            self._config_mgr = ConfigManager(key=validate_and_get_mk(prompt="Please enter a Master Key to encrypt your passkeys."))
            self._config = Config([])
            self._config_mgr.save_config(self._config)

            self._notification_handler.info("The credentials file created.")

    def add_item(self, window: WindowConfig, __save: bool = True) -> None:
        """add a new item in the tree"""

        item: QtGui.QStandardItemModel | QtGui.QStandardItem

        if window.group is None:
            item = self.model
        else:
            root = self.model.invisibleRootItem()
            if root is None:
                return

            for row in range(root.rowCount()):
                child = root.child(row)
                if isinstance(child, QStandardPasskeyItem) and child.window is None and child.text() == window.group:
                    item = child
                    break
            else:
                item = QStandardPasskeyItem(window.group, window=None)
                self.model.appendRow(item)

        sub_item = QStandardPasskeyItem(window.name, window=window)
        item.appendRow(sub_item)

        if __save:
            self._config.windows.append(window)
            self._config_mgr.save_config(self._config)

    def move_item(self, current_item: QStandardPasskeyItem, target_item: QStandardPasskeyItem | None, __save: bool = True) -> None:
        """move the item to another location"""

        cloned_item = QStandardPasskeyItem.clone_from(current_item)

        (current_item.parent() or self.model).removeRow(current_item.row())
        (target_item or self.model).appendRow(cloned_item)

        if current_item.window:
            current_item.window.group = None if target_item is None else target_item.text()

        if __save:
            self._config_mgr.save_config(self._config)

    def _delete_item_dialog(self, item: QStandardPasskeyItem) -> bool:
        """show a popup to the user and get the response. returns True if user wants to delete the item."""
        title = "Delete Item"
        if item.window is None:
            message = f"Are you sure you want to delete '{self.ui.tree.currentIndex().data()}' and all of its content?"
        else:
            message = f"Are you sure you want to delete '{item.window.name}'?"

        answer = QtWidgets.QMessageBox.question(self.ui.tree, title, message + "\n\nThis operation is irreversible.")

        return answer == QtWidgets.QMessageBox.StandardButton.Yes

    def remove_item(self, item: QStandardPasskeyItem, __save: bool = True, *, show_dialog: bool = True) -> None:
        """remove the item from the config"""

        current_index = self.ui.tree.currentIndex()
        if current_index is None:
            raise ValueError("No item is selected")

        if show_dialog and not self._delete_item_dialog(item):
            return

        if item.window is None:
            # delete parent
            sub_items = [
                item.child(row) for row in range(item.rowCount())
            ]  # get items first, otherwise order is changing and causes problems
            for sub_item in sub_items:
                if sub_item is None:
                    continue
                item.removeRow(sub_item.row())
                if isinstance(sub_item, QStandardPasskeyItem) and sub_item.window is not None:
                    self._config.windows.remove(sub_item.window)
            self.model.removeRow(current_index.row())
        else:
            parent_item: QtGui.QStandardItem | QtGui.QStandardItemModel = self.model
            if item.window.group is not None:
                item_from_index = self.model.itemFromIndex(current_index.parent())
                if item_from_index is None:
                    raise ValueError("item did not exist.")
                parent_item = item_from_index

            parent_item.removeRow(current_index.row())
            self._config.windows.remove(item.window)

        if __save:
            self._config_mgr.save_config(self._config)

        self._refresh()

    def update_window(self, window: WindowConfig, title: str, name: str, passkey: str) -> None:
        """update the window data and save the config"""

        window.title = title
        window.name = name
        window.passkey = passkey + "\n"

        self._config_mgr.save_config(self._config)
        self._refresh()

    def render(self) -> None:
        """render the widgets"""

        self.ui.tree.setHeaderHidden(True)
        self.ui.tree.setModel(self.model)

        for group_name, windows in self._config.group().items():
            if group_name is not None:
                item = QStandardPasskeyItem(group_name, window=None)
                self.model.appendRow(item)

            for window in windows:
                self.add_item(window, False)

        Hooks(self).hook()
        self._handler.bind()

    def loop(self) -> None:
        """start the loop"""

        app = QtWidgets.QApplication([])
        main_window = QtWidgets.QMainWindow()

        self.ui.setupUi(main_window)
        self.render()

        main_window.show()
        sys.exit(app.exec())


class Notification:
    """show a notification to the user"""

    @staticmethod
    def show_message(
        widget: QtWidgets.QWidget, message: str, title: str, *, info: str | None = None, icon: QtWidgets.QMessageBox.Icon
    ) -> None:
        """show a notification message to the user. the icon changes the message type"""

        error_message = QtWidgets.QMessageBox(widget)
        error_message.setIcon(icon)
        error_message.setText(message)
        if info:
            error_message.setInformativeText(info)
        error_message.setWindowTitle(title)
        error_message.show()

    @classmethod
    def show_error(cls, widget: QtWidgets.QWidget, message: str, title: str, *, info: str | None = None) -> None:
        """show an error message"""
        cls.show_message(widget=widget, message=message, title=title, info=info, icon=QtWidgets.QMessageBox.Icon.Critical)


class AddItemDialog:
    """a dialog widget to get user input for adding a new item"""

    class Data(TypedDict):
        """the return data of AddItemDialog"""

        group: str | None
        name: str
        title: str

    def __init__(self, groups: List[str]) -> None:
        self._groups = groups

        self._wrapper_widget = QtWidgets.QWidget()
        self._wrapper_widget.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        self._ui = Ui_AddItemWidget()
        self._ui.setupUi(self._wrapper_widget)

        self._data: AddItemDialog.Data | None = None

    def setup(self) -> None:
        """setup the dialog"""

        self._wrapper_widget.setWindowTitle("Add New Item")

        self._ui.dropdown_group.addItem("No group")
        self._ui.dropdown_group.addItems(self._groups)
        self._ui.dropdown_group.addItem("Create new...")

        italic_font = QtGui.QFont("Times", italic=True)
        self._ui.dropdown_group.setItemData(0, italic_font, QtCore.Qt.ItemDataRole.FontRole)
        self._ui.dropdown_group.setItemData(len(self._groups) + 1, italic_font, QtCore.Qt.ItemDataRole.FontRole)

    def get_data(self, selected: str | None = None) -> Data | None:
        """show the add item dialog and return the data if OK clicked."""

        self.setup()
        index = self._ui.dropdown_group.findText(selected)
        if index != -1:
            self._ui.dropdown_group.setCurrentIndex(index)

        self.loop()

        return self._data

    def _cancel(self) -> None:
        self._data = None
        self._wrapper_widget.destroyed.emit()

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

    def _save(self) -> None:
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

        self._data = AddItemDialog.Data(group=group, name=name, title=title)

        self._wrapper_widget.destroyed.emit()

    def loop(self) -> None:
        """create an event loop and wait until window closes"""
        self._wrapper_widget.show()

        loop = QtCore.QEventLoop()

        self._wrapper_widget.destroyed.connect(loop.quit)
        self._ui.button_cancel.clicked.connect(self._cancel)
        self._ui.button_ok.clicked.connect(self._save)

        loop.exec()


class SignalHandler:
    """signal handlers"""

    def __init__(self, manager: PasswordManagerUI) -> None:
        self._manager = manager
        self._old_item: QStandardPasskeyItem | None = None

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

    def _check_is_saved(self) -> bool:
        if self._old_item is None or self._old_item.window is None:
            return True

        item_compare_map = (
            ("title", self._old_item.window.title, self._manager.ui.entry_title.text()),
            ("name", self._old_item.window.name, self._manager.ui.entry_name.text()),
            ("password", self._old_item.window.passkey[:-1], self._manager.ui.entry_password.text()),
        )

        for name, old_value, new_value in item_compare_map:
            if new_value != old_value:
                question = QtWidgets.QMessageBox.question(
                    self._manager.ui.tree, "Are you sure?", f"The {name} has been changed and not saved. Are you sure to discard?"
                )
                if question == QtWidgets.QMessageBox.StandardButton.Yes:
                    return True
                self._manager.ui.tree.setCurrentIndex(self._manager.model.indexFromItem(self._old_item))
                return False
        return True

    def load_window_config(self, index: QtCore.QModelIndex) -> None:
        """load the config widget based on selected item"""

        if not self._check_is_saved():
            return

        self._old_item = self.get_current_item(index)
        window = self._old_item.window

        items = (
            (self._manager.ui.entry_title, True),
            (self._manager.ui.entry_name, True),
            (self._manager.ui.entry_password, True),
            (self._manager.ui.checkbox_toggle_password, False),
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
        self._manager.ui.entry_password.setText(window.passkey[:-1])

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

        data = AddItemDialog(groups).get_data(selected_group)
        if data is not None:
            self._manager.add_item(WindowConfig(**data, passkey=""))

    def delete_item(self) -> None:
        """delete the selected item from the tree"""
        current_item = self.get_current_item()

        self._manager.remove_item(current_item)

    def save_item(self) -> None:
        """save all configuration for given item"""

        title = self._manager.ui.entry_title.text()
        name = self._manager.ui.entry_name.text()
        passkey = self._manager.ui.entry_password.text()

        for value, value_str in ((title, "title"), (name, "name")):
            if not value:
                Notification.show_error(self._manager.ui.tree, f"The {value_str} cannot left empty", f"Empty {value_str}".title())
                return

        window = self.get_current_item().window
        if window:
            self._manager.update_window(window, title, name, passkey)

    def bind(self) -> None:
        """bind signals"""

        self._manager.ui.checkbox_toggle_password.stateChanged.connect(self.toggle_password)
        self._manager.ui.tree.clicked.connect(self.set_controller_visibility)
        self._manager.ui.tree.clicked.connect(self.load_window_config)

        self._manager.ui.button_add_item.clicked.connect(self.add_item_dialog)
        self._manager.ui.button_delete_item.clicked.connect(self.delete_item)

        self._manager.ui.button_save.clicked.connect(self.save_item)


if __name__ == "__main__":
    PasswordManagerUI().loop()

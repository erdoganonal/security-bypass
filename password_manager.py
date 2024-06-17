"""a UI to manage the passwords"""

# pylint: disable=c-extension-no-member

import sys
import warnings
from typing import Any

from PyQt6 import QtCore, QtGui, QtWidgets

from common.exit_codes import ExitCodes
from common.tools import check_single_instance
from config.config import Config, ConfigManager, WindowData
from config.config_key_manager import check_config_file, validate_and_get_mk
from generated.ui_generated_main import Ui_MainWindow  # type: ignore[attr-defined]
from helpers.ui_helpers.altered import QStandardPasskeyItem
from helpers.ui_helpers.pm.handlers.signal_handler import SignalHandler
from notification_handler.gui import GUINotificationHandler

warnings.filterwarnings("ignore", category=DeprecationWarning)


class Hooks:
    """allows to to customized actions on specific methods"""

    def __init__(self, manager: "PasswordManagerUI") -> None:
        self._manager = manager

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

    def change_master_key(self, new: str) -> None:
        """change the master key"""

        self._config_mgr.change_master_key(new.encode())

    def get_config(self) -> Config:
        """return the config object"""
        return self._config

    def add_item(self, window: WindowData, __save: bool = True) -> None:
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

    def update_window(self) -> None:
        """update the window data and save the config"""

        self._config_mgr.save_config(self._config)
        self._refresh()

    def rerender(self, key: bytes, config: Config) -> None:
        """re-render the widgets"""

        self.model.clear()
        self._config_mgr = ConfigManager(key=key)
        self._config = config

        for group_name, windows in self._config.group().items():
            if group_name is not None:
                item = QStandardPasskeyItem(group_name, window=None)
                self.model.appendRow(item)

            for window in windows:
                self.add_item(window, False)

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


if __name__ == "__main__":
    check_single_instance()

    PasswordManagerUI().loop()

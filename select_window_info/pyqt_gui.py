"""show an dialog popup to the user and let them pick a password"""

# pylint: disable=c-extension-no-member
from typing import Sequence

from pygetwindow import PyGetWindowException, Win32Window  # type: ignore[import-untyped]
from PyQt6 import QtCore, QtGui, QtWidgets

try:
    # pylint: disable=unused-import
    import __path_fixer__  # type: ignore[import-not-found]
except ImportError:
    pass

from common.tools import focus_window, get_position, get_window_by_hwnd
from config.config import WindowData
from generated.ui_generated_get_passkey_dialog import Ui_PasskeyDialog  # type: ignore[attr-defined]
from select_window_info.base import SelectWindowInfoBase
from select_window_info.multithread_support import main_execute, thread_execute


class _PyQtGUISelectWindowInfoHelper:
    """Select the window by using PyQt GUI"""

    def __init__(self) -> None:
        self._app = QtWidgets.QApplication([])
        self._main_window = QtWidgets.QMainWindow()
        self._ui = Ui_PasskeyDialog()

        self._model = QtGui.QStandardItemModel()

        self._selected_index: int | None = None
        self._send_enter: bool = True

        self._main_window.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)

        self._ui.setupUi(self._main_window)

        self._ui.list_view.setModel(self._model)
        self._ui.list_view.setEditTriggers(QtWidgets.QAbstractItemView.EditTrigger.NoEditTriggers)

        self._timer = QtCore.QTimer(self._main_window)

    def get(self, windows_data: Sequence[WindowData]) -> WindowData | None:
        """return the selected value and the send enter value"""

        if self._selected_index is None:
            return None

        return windows_data[self._selected_index]

    def add_item(self, item: str) -> None:
        """add a new item into the list"""

        self._model.appendRow(QtGui.QStandardItem(item))

    def accept(self) -> None:
        """accept the user response and close the window"""

        indexes = self._ui.list_view.selectedIndexes()
        if indexes:
            self._selected_index = indexes[0].row()

        self._send_enter = self._ui.checkbutton_send_enter.isChecked()

        self._app.quit()

    def reject(self) -> None:
        """close the window"""

        self._selected_index = None

        self._app.quit()

    def _update(self, window: Win32Window | None) -> None:
        if window is None:
            return

        try:
            left, top = get_position(window)
        except PyGetWindowException:
            self._app.quit()

        window = get_window_by_hwnd(int(self._main_window.winId()))
        if window:
            window.moveTo(left, top)

    def select(self, window_hwnd: int, windows_data: Sequence[WindowData]) -> WindowData | None:
        """Let user to pick the password from the list"""

        for window_data in windows_data:
            self.add_item(window_data.name)

        window = get_window_by_hwnd(window_hwnd)
        if window is not None:
            focus_window(window)

        self._timer.timeout.connect(lambda w=window: self._update(w))
        self._timer.start(1000)
        self.render()

        return self.get(windows_data)

    def render(self) -> None:
        """start the app and render"""

        self._ui.buttonbox_ok_cancel.accepted.connect(self.accept)
        self._ui.buttonbox_ok_cancel.rejected.connect(self.reject)

        self._ui.list_view.doubleClicked.connect(lambda _: self.accept())

        self._main_window.show()
        self._app.exec()


class PyQtGUISelectWindowInfo(SelectWindowInfoBase):
    """Select the window by using PyQt GUI"""

    @property
    def supports_thread(self) -> bool:
        return True

    def select(self, window_hwnd: int, windows_data: Sequence[WindowData]) -> WindowData | None:
        if not windows_data:
            return None

        # even if the operation runs in main thread, the pyqt gui acts strangely.
        # to overcome this, there is no direct call for _PyQtGUISelectWindowInfoHelper.select
        return thread_execute(__file__, window_hwnd, windows_data)


if __name__ == "__main__":
    main_execute(_PyQtGUISelectWindowInfoHelper())

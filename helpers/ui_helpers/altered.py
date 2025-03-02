"""Customized PyQt classes"""

# pylint: disable=c-extension-no-member

from ctypes import windll

from PyQt6 import QtCore, QtGui, QtWidgets

from config.config import WindowData


# pylint: disable=too-few-public-methods
class QStandardPasskeyItem(QtGui.QStandardItem):
    """customized q-item for window config"""

    def __init__(self, text: str, window: WindowData | None) -> None:
        super().__init__(text)
        self.window = window

    @classmethod
    def clone_from(cls, item: "QStandardPasskeyItem") -> "QStandardPasskeyItem":
        """clone a QStandardPasskeyItem and return as a new item"""

        return cls(text=item.text(), window=item.window)


class AlwaysOnTopWindow(QtWidgets.QMainWindow):
    """Window that stays on top of all other windows"""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(QtCore.Qt.WindowType.WindowStaysOnTopHint)

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self._bring_to_front)
        self.timer.start(100)  # Check every second

    def _bring_to_front(self) -> None:
        if int(self.winId()) != windll.user32.GetForegroundWindow():
            self.showMinimized()
            self.showNormal()

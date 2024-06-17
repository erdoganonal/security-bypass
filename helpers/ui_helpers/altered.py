"""Customized PyQt classes"""

# pylint: disable=c-extension-no-member

from PyQt6 import QtGui

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

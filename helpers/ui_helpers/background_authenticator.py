"""Background authenticator UI helper."""

# pylint: disable=c-extension-no-member

import abc
from typing import TypedDict

from PyQt6 import QtCore, QtGui, QtWidgets

from generated.ui_generated_background_authenticator import Ui_BackgroundAuthenticator  # type: ignore[attr-defined]
from helpers.ui_helpers.altered import AlwaysOnTopWindow


class BgWindowData(TypedDict):
    """Background window data."""

    window_title: str
    title: str
    info: str
    icon_path: str


class BackgroundAuthenticatorBase(abc.ABC):
    """Abstract class for background authentication."""

    def __init__(self) -> None:
        self.app = QtWidgets.QApplication([])
        self.app.setStyle("windowsvista")

        self.main_window = AlwaysOnTopWindow()
        self.ui = Ui_BackgroundAuthenticator()
        self.ui.setupUi(self.main_window)

    @abc.abstractmethod
    def get_window_data(self) -> BgWindowData:
        """Get the window data of the background authenticator."""

    def show(self) -> None:
        """Show the background authenticator."""

        window_data = self.get_window_data()
        self.main_window.setWindowTitle(window_data["window_title"])
        self.ui.label_title.setText(window_data["title"])
        self.ui.label_info.setText(window_data["info"])
        self.ui.label_icon.setPixmap(QtGui.QPixmap(window_data["icon_path"]))

        self.main_window.show()
        self.app.exec()

    def thread_quit(self) -> None:
        """Quit the application from another thread."""

        QtCore.QMetaObject.invokeMethod(self.app, "quit", QtCore.Qt.ConnectionType.QueuedConnection)

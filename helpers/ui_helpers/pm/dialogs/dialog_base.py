"""includes the base class for all dialogs"""

# pylint: disable=c-extension-no-member


import abc
from typing import Any, Generic, Protocol, Type, TypeVar

from PyQt6 import QtCore, QtWidgets


# pylint: disable=too-few-public-methods
class SupportsSetupUi(Protocol):
    """a protocol class to force the implementation of setupUi method"""

    def setupUi(self, widget: QtWidgets.QWidget) -> None:
        """protocol function or method called setupUi"""


T = TypeVar("T", bound=Any)
T1 = TypeVar("T1", bound=SupportsSetupUi)


class _QWidgetWrapper(QtWidgets.QWidget):
    """a wrapper class for QWidget"""

    def __init__(self, dialog_base: "DialogBase[Any, Any]") -> None:
        self._base = dialog_base
        super().__init__()

    def accept(self) -> None:
        """accept function"""
        self._base.accept()

    def reject(self) -> None:
        """reject function"""
        self._base.reject()


class DialogBase(Generic[T, T1], abc.ABC):
    """base class for all dialogs"""

    def __init__(self) -> None:
        self._wrapper_widget = _QWidgetWrapper(self)
        self._wrapper_widget.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)

        self._ui = self.skeleton()
        self._ui.setupUi(self._wrapper_widget)

        self._data: T | None = None

    @property
    @abc.abstractmethod
    def skeleton(self) -> Type[T1]:
        """return the skeleton of the dialog"""

    @abc.abstractmethod
    def accept(self) -> None:
        """this function is called when OK button is pressed"""

    def close(self) -> None:
        """close the dialog"""
        self._wrapper_widget.destroyed.emit()
        self._wrapper_widget.close()

    def reject(self) -> None:
        """this function is called when Cancel button is pressed"""
        self._data = None
        self.close()

    def configure(self) -> None:
        """configure the dialog"""

    def get(self) -> T | None:
        """return the data of the dialog"""
        self.configure()
        self.loop()
        return self._data

    def loop(self) -> None:
        """show the dialog an wait until the user closes it"""

        loop = QtCore.QEventLoop()

        self._wrapper_widget.show()
        self._wrapper_widget.destroyed.connect(loop.quit)
        loop.exec()

"""Notification class to show messages to the user"""

# pylint: disable=c-extension-no-member

from PyQt6 import QtWidgets


class Notification:
    """show a notification to the user"""

    @staticmethod
    def _prepare_message(
        widget: QtWidgets.QWidget, message: str, title: str, *, info: str | None = None, icon: QtWidgets.QMessageBox.Icon
    ) -> QtWidgets.QMessageBox:
        """prepare a notification message to the user. the icon changes the message type"""

        message_box = QtWidgets.QMessageBox(widget)
        message_box.setIcon(icon)
        message_box.setText(message)
        if info:
            message_box.setInformativeText(info)
        message_box.setWindowTitle(title)

        return message_box

    @classmethod
    def show_info(cls, widget: QtWidgets.QWidget, message: str, title: str, *, info: str | None = None) -> None:
        """show an info message"""
        cls._prepare_message(widget=widget, message=message, title=title, info=info, icon=QtWidgets.QMessageBox.Icon.Information).show()

    @classmethod
    def ask_yes_no(cls, widget: QtWidgets.QWidget, message: str, title: str, *, info: str | None = None) -> bool:
        """show a yes/no message and return the response"""
        msg = cls._prepare_message(widget=widget, message=message, title=title, info=info, icon=QtWidgets.QMessageBox.Icon.Question)
        msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        return msg.exec() == QtWidgets.QMessageBox.StandardButton.Yes

    @classmethod
    def show_warning(cls, widget: QtWidgets.QWidget, message: str, title: str, *, info: str | None = None) -> None:
        """show a warning message"""
        cls._prepare_message(widget=widget, message=message, title=title, info=info, icon=QtWidgets.QMessageBox.Icon.Warning).show()

    @classmethod
    def show_error(cls, widget: QtWidgets.QWidget, message: str, title: str, *, info: str | None = None) -> None:
        """show an error message"""
        cls._prepare_message(widget=widget, message=message, title=title, info=info, icon=QtWidgets.QMessageBox.Icon.Critical).show()

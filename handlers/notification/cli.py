"""CLI notification handler"""

import getpass
import sys

from handlers.notification.base import MessageType, NotificationInterface


class NotificationCLI(NotificationInterface):
    """Print messages to the console"""

    def __init__(self, message_format: str = "{title}: {message}") -> None:
        self._message_format = message_format

    def ask_yes_no(self, message: str, title: str = "") -> bool:
        question = self._message_format.format(message=message, title=title) + " (y/N)"
        return self.user_input(question).strip() == "y"

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        if msg_type in (MessageType.ERROR, MessageType.CRITICAL):
            target = sys.stderr
        else:
            target = sys.stdout

        print(self._message_format.format(message=message, title=title), file=target)

    def user_input(self, message: str, title: str = "", hidden_text: bool = False) -> str:
        if hidden_text:
            return getpass.getpass(f"{message}: ")
        return input(f"{message}: ")

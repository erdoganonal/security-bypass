"""CLI notification handler"""


import sys

from notification_handler.base import MessageType, NotificationHandlerBase


class CLINotificationHandler(NotificationHandlerBase):
    """Print messages to the console"""

    def __init__(self, message_format: str = "{title}: {message}") -> None:
        self._message_format = message_format

    def show(self, message: str, title: str, msg_type: MessageType) -> None:
        if msg_type in (MessageType.ERROR, MessageType.CRITICAL):
            target = sys.stderr
        else:
            target = sys.stdout

        print(self._message_format.format(message=message, title=title), file=target)

"""Common function/methods"""
import psutil


def is_windows_locked() -> bool:
    """Return the lock information of the windows"""

    for proc in psutil.process_iter():
        if proc.name() == "LogonUI.exe":
            return True
    return False


class InplaceInt:
    """an integer that the value of it can be changed(mutable)"""

    def __init__(self, value: int = 0) -> None:
        self._value = value

    def get(self) -> int:
        """return the value of this instance"""

        return self._value

    def set(self, value: int = 0) -> None:
        """set the value to given one"""

        self._value = value

    def get_and_increment(self, by: int = 0) -> int:
        """return the value and increment by given value"""

        value = self._value
        self._value += by
        return value

    def increment_and_get(self, by: int = 0) -> int:
        """increment by given value and return"""

        self._value += by
        return self._value

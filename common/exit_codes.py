"""exit codes and their meaning"""

import enum
import sys
from typing import NoReturn


class ExitCodes(enum.IntEnum):
    """enumeration for exit codes"""

    UNKNOWN = enum.auto()
    ALREADY_RUNNING = enum.auto()
    CREDENTIAL_FILE_DOES_NOT_EXIST = enum.auto()
    EMPTY_MASTER_KEY = enum.auto()
    WRONG_MASTER_KEY = enum.auto()

    def exit(self) -> NoReturn:
        """same as sys.exit but gives the exit code"""

        sys.exit(self.value)

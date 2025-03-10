"""exit codes and their meaning"""

import enum
import sys
from typing import NoReturn

from logger import logger


class ExitCodes(enum.IntEnum):
    """enumeration for exit codes"""

    SUCCESS = 0
    UNKNOWN = enum.auto()
    ALREADY_RUNNING = enum.auto()
    CREDENTIAL_FILE_DOES_NOT_EXIST = enum.auto()
    EMPTY_MASTER_KEY = enum.auto()
    WRONG_MASTER_KEY = enum.auto()
    WRONG_MASTER_KEY_FORMAT = enum.auto()
    RESTARTED_AS_ADMIN = enum.auto()
    WINBIO_ERROR = enum.auto()
    USER_CANCELLED = enum.auto()

    def exit(self) -> NoReturn:
        """same as sys.exit but gives the exit code"""

        logger.error("Exiting with code %s", self.name)
        sys.exit(self.value)

    @classmethod
    def get_name(cls, code: "int | str | None | ExitCodes") -> str:
        """return the name of the given code"""
        if isinstance(code, ExitCodes):
            return code.name

        if not isinstance(code, int):
            return cls.UNKNOWN.name

        return cls(code).name

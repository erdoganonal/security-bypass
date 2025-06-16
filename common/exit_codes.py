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

    @staticmethod
    def get_explanation(code: "ExitCodes") -> str:
        """return the explanation of the given code"""
        try:
            return _EXIT_CODES_EXPLANATIONS[code]
        except KeyError:
            return _EXIT_CODES_EXPLANATIONS[ExitCodes.UNKNOWN]


_EXIT_CODES_EXPLANATIONS = {
    ExitCodes.SUCCESS: "The operation completed successfully.",
    ExitCodes.UNKNOWN: "An unknown error occurred. Please check the logs for more details.",
    ExitCodes.ALREADY_RUNNING: "The application is already running.",
    ExitCodes.CREDENTIAL_FILE_DOES_NOT_EXIST: "The credential file does not exist. Please create it first.",
    ExitCodes.EMPTY_MASTER_KEY: "The master key is empty. Please provide a valid master key.",
    ExitCodes.WRONG_MASTER_KEY: "The provided master key is incorrect. Please try again.",
    ExitCodes.WRONG_MASTER_KEY_FORMAT: "The master key format is incorrect. Please provide a valid key.",
    ExitCodes.RESTARTED_AS_ADMIN: "The application has been restarted with administrative privileges.",
    ExitCodes.WINBIO_ERROR: "An error occurred with the Windows Biometric Framework. Please check your biometric device.",
    ExitCodes.USER_CANCELLED: "The operation was cancelled by the user.",
}

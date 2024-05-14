"""setup the environment for the first usage"""

import os
import subprocess
import sys
from getpass import getpass
from pathlib import Path
from typing import NoReturn, overload

try:
    import win32api

    from config.config import Config, ConfigManager
    from config.config_key_manager import check_config_file
    from settings import DFT_ENCODING
except ImportError:
    RESTART = True
else:
    RESTART = False

try:
    from colorama import Fore
except ImportError:
    # pylint: disable=too-few-public-methods
    class Fore:  # type: ignore[no-redef]
        """fake fore"""

        GREEN = ""
        BLUE = ""
        RESET = ""


SCRIPT_DIR = Path(__file__).parent

REQUIREMENT_FILE = "requirements.txt"
TASK_SCHEDULER_XML = "Security Bypass.xml"
TASK_TEMP_SCHEDULER_XML = "temp.xml"


def main() -> None:
    """starts from here"""

    install_requirements()

    if RESTART:
        restart()

    adjust_task_scheduler_xml()

    initial_setup()

    _system('schtasks /run /tn "Security Bypass"')

    InputOutputHelper.info("\nInstallation completed. Please add your passkeys using 'python password_manager.py'")


def _system(cmd: str, error_message: str = "") -> None:
    exit_code = os.system(cmd)
    if exit_code != 0:
        if error_message:
            if RESTART:
                print(error_message, file=sys.stderr)
            else:
                InputOutputHelper.error(error_message, exit_code=exit_code)
        sys.exit(exit_code)


def install_requirements() -> None:
    """install required python libraries"""

    if RESTART:
        InputOutputHelper.info("installing requirements, please wait...")
    _system(
        f'"{sys.executable}" -m pip install -r {REQUIREMENT_FILE} -q -q -q --exists-action i',
        "cannot install one or more packages with pip",
    )
    if not RESTART:
        InputOutputHelper.info("requirements have been installed.\n")


def restart() -> None:
    """restart the application"""

    python = sys.executable
    with subprocess.Popen(f"{python} {' '.join(sys.argv)}") as process:
        pass
    sys.exit(process.returncode)


def adjust_task_scheduler_xml() -> None:
    """open the xml file and replace the content for current user"""

    with open(TASK_SCHEDULER_XML, "r", encoding="utf-16") as xml_fd:
        xml_content = xml_fd.read()

    xml_content = xml_content.format(
        username=win32api.GetUserNameEx(win32api.NameSamCompatible),  # pylint: disable=c-extension-no-member
        pythonw=next(Path(sys.executable).parent.glob("pythonw.exe")),
        script_dir=SCRIPT_DIR,
    )

    with open(TASK_TEMP_SCHEDULER_XML, "w", encoding="utf-16") as temp_xml_fd:
        temp_xml_fd.write(xml_content)

    try:
        _system(f'schtasks /create /xml "{TASK_TEMP_SCHEDULER_XML}" /tn "Security Bypass"')
    finally:
        os.unlink(TASK_TEMP_SCHEDULER_XML)


class ContinueLoopError(Exception):
    """This is a fake error. When this error is raised the loop will continue"""


class InputOutputHelper:
    """Helper class to get the inputs from the user and show to the user."""

    @classmethod
    def ask_yes_no(cls, prompt: str, yes_no_str: str = "[y/N]: ", yes: str = "y") -> bool:
        """A standard way to get user yes/no response"""
        return input(prompt + yes_no_str) == yes

    @classmethod
    def ask_title(cls) -> str:
        """A standard way to get the title from the user"""
        return input("Please enter the title or title pattern: ")

    @classmethod
    def ask_name(cls) -> str:
        """A standard way to get the name from the user"""
        return input("Please enter a name for your key: ")

    @classmethod
    def ask_password(cls, prompt: str = "Please enter the new passkey", validate: bool = True) -> str:
        """A standard way to get the passkey from the user"""
        passkey = getpass(f"{prompt}: ")
        if validate:
            passkey_validation = getpass(f"{prompt} again: ")

            if passkey != passkey_validation:
                cls.error("\nValues did not match!")
                raise ContinueLoopError

        return passkey + "\n"

    @classmethod
    def title(cls, prompt: str) -> None:
        """A standard way to print an info message"""
        print(Fore.BLUE + prompt + Fore.RESET)

    @classmethod
    def info(cls, prompt: str) -> None:
        """A standard way to print an info message"""
        print(Fore.GREEN + prompt + Fore.RESET)

    @classmethod
    def warning(cls, prompt: str) -> None:
        """A standard way to print an warning message"""
        print(Fore.YELLOW + prompt + Fore.RESET)

    @overload
    @classmethod
    def error(cls, prompt: str, exit_code: None = None) -> None:
        pass

    @overload
    @classmethod
    def error(cls, prompt: str, exit_code: int) -> NoReturn:
        pass

    @classmethod
    def error(cls, prompt: str, exit_code: int | None = None) -> None:
        """A standard way to print an error message"""
        print(Fore.RED + prompt + Fore.RESET, file=sys.stderr)
        if exit_code is not None:
            sys.exit(exit_code)


def _get_password() -> str:
    while True:
        try:
            return InputOutputHelper.ask_password("Please enter a Master Key to encrypt your passkeys")
        except ContinueLoopError:
            continue


def initial_setup() -> None:
    """do initial setup"""

    try:
        check_config_file()
    except FileNotFoundError:
        pass
    else:
        return

    print()
    key = _get_password()
    config_mgr = ConfigManager(key=key.encode(encoding=DFT_ENCODING))
    config_mgr.save_config(Config([]))

    InputOutputHelper.info("\nan empty configuration file has been created.\n")

    # with subprocess.Popen(f"{sys.executable} password_manager.py", env=os.environ | {MK_ENV_NAME: key}):
    #     pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit("\nOperation cancelled by user")

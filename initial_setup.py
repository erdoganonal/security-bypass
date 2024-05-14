"""setup the environment for the first usage"""

import os
import subprocess
import sys
from getpass import getpass
from pathlib import Path
from typing import NoReturn, overload

from settings import DFT_ENCODING, MK_ENV_NAME

try:
    import win32api

    from common.exit_codes import ExitCodes
    from common.password_validator import PASSWORD_SCHEMA, get_schema_rules
    from config.config import Config, ConfigManager
    from config.config_key_manager import check_config_file
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
        YELLOW = ""
        RED = ""
        RESET = ""


SCRIPT_DIR = Path(__file__).parent

REQUIREMENT_FILE = "requirements.txt"
TASK_SCHEDULER_XML = "Security Bypass.xml"
TASK_TEMP_SCHEDULER_XML = "temp.xml"

DESCRIPTION = """Security Bypass

You can easily enter your passwords without touching the keyboard.
It is one click a way.

Error Codes and reasons:
{unknown} -> The application faced an unknown issue. Most probably a bug.
{already_running} -> Another instance of the application is already running. Stop it and run the task again.
{credential_file_not_exists} -> The credential file does not found. Use the 'password_manager.py' to create it.
{empty_key} -> The master key that is entered is empty. An empty master key is not allowed.
{wrong_key} -> The master key that is entered is wrong. Please enter the correct one.
"""


def main() -> None:
    """starts from here"""

    # check_virtual_environment()

    install_requirements()

    if RESTART:
        restart()

    if is_update():
        print("\nCompleting the update process...")
        complete_update()

    adjust_task_scheduler_xml()

    initial_setup()

    _system('schtasks /run /tn "Security Bypass"')

    InputOutputHelper.info("\nInstallation completed")  # . Please add your passkeys using 'python password_manager.py'")


def _system(cmd: str, error_message: str = "") -> None:
    exit_code = os.system(cmd)
    if exit_code != 0:
        if error_message:
            InputOutputHelper.error(error_message, exit_code=exit_code)
        sys.exit(exit_code)


def check_virtual_environment() -> None:
    """check whether the script is running in a virtual environment or not"""

    if os.getenv("VIRTUAL_ENV"):
        InputOutputHelper.error("Running the installation script in a virtual environment is not allowed.", exit_code=-1)


def install_requirements() -> None:
    """install required python libraries"""

    if RESTART:
        InputOutputHelper.info("installing requirements, please wait...")
    _system(
        f'"{sys.executable}" -m pip install -r {REQUIREMENT_FILE} -q -q -q --exists-action i',
        "cannot install one or more packages with pip",
    )
    if not RESTART:
        InputOutputHelper.info("The required libraries have been installed.\n")


def restart() -> None:
    """restart the application"""

    python = sys.executable
    with subprocess.Popen(f"{python} {' '.join(sys.argv)}") as process:
        pass
    sys.exit(process.returncode)


def is_update() -> bool:
    """check whether the application is updated or not"""

    return os.system('schtasks /query /tn "Security Bypass"') == 0


def complete_update() -> NoReturn:
    """complete the update process by stopping and starting again the task scheduler"""

    _system('schtasks /end /tn "Security Bypass"')
    pid = subprocess.check_output(
        """wmic process where "commandline like '%security_bypass_wrapper.py%' and not commandline like 'wmic%%'" get processid""",
        text=True,
        stderr=subprocess.PIPE,
    ).splitlines()[2]

    if pid:
        _system(f"taskkill /f /pid {pid}")

    _system('schtasks /run /tn "Security Bypass"')

    InputOutputHelper.info("\nUpdate completed.")
    sys.exit(0)


def adjust_task_scheduler_xml() -> None:
    """open the xml file and replace the content for current user"""

    with open(TASK_SCHEDULER_XML, "r", encoding="utf-16") as xml_fd:
        xml_content = xml_fd.read()

    xml_content = xml_content.format(
        username=win32api.GetUserNameEx(win32api.NameSamCompatible),  # pylint: disable=c-extension-no-member
        pythonw=next(Path(sys.executable).parent.glob("pythonw.exe")),
        description=DESCRIPTION.format(
            unknown=ExitCodes.UNKNOWN.value,
            already_running=ExitCodes.ALREADY_RUNNING.value,
            credential_file_not_exists=ExitCodes.CREDENTIAL_FILE_DOES_NOT_EXIST,
            empty_key=ExitCodes.EMPTY_MASTER_KEY.value,
            wrong_key=ExitCodes.WRONG_MASTER_KEY.value,
        ),
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

        return passkey

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
            password = InputOutputHelper.ask_password("Please enter a Master Key to encrypt your passkeys")
            if PASSWORD_SCHEMA.validate(password):
                return password
            InputOutputHelper.warning(get_schema_rules(PASSWORD_SCHEMA))
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

    subprocess.check_output(f"{sys.executable} password_manager.py", env=os.environ | {MK_ENV_NAME: key})


def rollback() -> None:
    """rollback the changes"""

    os.system('schtasks /delete /tn "Security Bypass" /F')


if __name__ == "__main__":
    DO_ROLLBACK = True
    try:
        main()
        DO_ROLLBACK = False
    except KeyboardInterrupt:
        sys.exit("\nOperation cancelled by user")
    except SystemExit as err:
        if err.code == 0:
            DO_ROLLBACK = False
    finally:
        if DO_ROLLBACK:
            rollback()

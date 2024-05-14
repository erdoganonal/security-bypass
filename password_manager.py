"""Helps you to manage the passwords"""

import collections
import os
import sys
import time
from getpass import getpass
from typing import Any, Callable, Dict, List, NoReturn, overload

import colorama

from config import ConfigManager
from config.config import Config, WindowConfig
from config.config_key_manager import check_config_file, validate_and_get_mk
from settings import DFT_ENCODING, PASSWORD_REQUIRED_FILE_PATH

ASK_SEND_ENTER = "--ask-send-enter" in sys.argv
GREETINGS = "\nWelcome to Password Manager. You can easily manage your passkeys."


def main() -> None:
    """starts from here"""
    colorama.init()

    PasswordManager().loop()


class ContinueLoopError(Exception):
    """This is a fake error. When this error is raised the loop will continue"""


class PasswordManager:
    """Helper class for manage passwords"""

    def __init__(self) -> None:
        self._name_action_map: Dict[str, Callable[[], Any]] = {
            "Show Passkeys": self.show_passwords,
            "Show Passkeys Names": self.show_pwd_names,
            "Add New Passkey": self.add_new_pwd,
            "Delete a Passkey": self.delete_pwd,
            "Change a Passkey": self.change_pwd,
            "List Passkey Titles": self.list_titles,
            "Delete Passkey Title": self.delete_title,
            "Change Master Key": self.change_mk,
            "Exit": self.exit,
        }

        self._idx_name_map = {str(idx): name for idx, name in enumerate(self._name_action_map, start=1)}
        self._is_active = False
        self._completer = Completer()

        try:
            check_config_file()

            self._config_mgr = ConfigManager(key=validate_and_get_mk())
            self._config = self._config_mgr.get_config()
        except ValueError:
            InputOutputHelper.error("Cannot load configurations. The Master Key is wrong.", exit_code=1)
        except KeyError as err:
            InputOutputHelper.error(err.args[0], exit_code=1)
        except FileNotFoundError:
            # Initial usage, create an empty config file
            self._config_mgr = ConfigManager(key=validate_and_get_mk(prompt="Please enter a Master Key to encrypt your passkeys."))
            self._config = Config([])
            self.__save_config()

            InputOutputHelper.info("The credentials file created.")

    def _get_user_input(self) -> None:
        print()
        space = int(max(self._idx_name_map, key=len))
        for idx, name in self._idx_name_map.items():
            extra = " " * (space - len(idx))
            print(f"{extra}[{idx}] {name}")

        response = input("\nSelect an action: ")
        try:
            self._name_action_map[self._idx_name_map[response]]()
        except KeyError as err:
            InputOutputHelper.error("Invalid action!")
            raise ContinueLoopError() from err

    def _loop(self) -> None:
        os.system("cls")
        InputOutputHelper.info(GREETINGS)

        while self._is_active:
            time.sleep(1)
            self._completer.clear()
            try:
                self._get_user_input()
            except ContinueLoopError:
                pass

    def loop(self) -> None:
        """Start a user input loop until KeyboardInterrupt is received"""
        if self._is_active:
            return

        self._is_active = True
        try:
            self._loop()
        except KeyboardInterrupt:
            self.exit()

    def __save_config(self) -> None:
        self._config_mgr.save_config(self._config)

    def __get_title(self, list_titles: bool = True) -> WindowConfig:
        if list_titles:
            self.list_titles()

        title = input("Please select the title: ")
        try:
            return next(window for window in self._config.windows if window.window_title == title)
        except StopIteration as err:
            InputOutputHelper.error("The Title does not exist!")
            raise ContinueLoopError() from err

    def _list_names(self, window: WindowConfig, add_auto_complete: bool = True) -> None:
        print("Available passkey names listed below:")
        for name in window.passkey_data:
            print(f" - {name}")
            if add_auto_complete:
                self._completer.add_new(name)

    def __get_name(self, window: WindowConfig, list_names: bool = True) -> str:
        if list_names:
            self._list_names(window)

        name = input("Please select the name: ")
        if name in window.passkey_data:
            return name

        InputOutputHelper.error("The name does not exist!")
        raise ContinueLoopError()

    def show_passwords(self) -> None:
        """Show the currently saved passwords"""
        if not self._config.windows:
            InputOutputHelper.error("\nThere is no title saved yet.")
            return
        print()
        print(self._config.to_user_str(name_only=False, color=True))

    def show_pwd_names(self) -> None:
        """Show the currently saved password names"""
        print()
        print(self._config.to_user_str(name_only=True, color=True, show_send_enter=ASK_SEND_ENTER))

    def add_new_pwd(self) -> None:
        """Add a new password"""
        self.list_titles()
        title = InputOutputHelper.ask_title()
        name = InputOutputHelper.ask_name()
        passkey = InputOutputHelper.ask_password(validate=True, ask_send_enter=True)

        print(f"title: {title}\nname: {name}")
        if not InputOutputHelper.ask_yes_no("Is the parameters correct?"):
            self.add_new_pwd()
            return

        try:
            window = next(window for window in self._config.windows if window.window_title == title)
            window.passkey_data[name] = passkey
        except StopIteration:
            self._config.windows.append(WindowConfig(window_title=title, passkey_data={name: passkey}))

        self.__save_config()
        InputOutputHelper.info("\nThe new passkey has been added successfully!")

    def delete_pwd(self) -> None:
        """Delete a passkey from the config file"""
        window = self.__get_title(list_titles=True)
        name = self.__get_name(window)

        del window.passkey_data[name]

        self.__save_config()
        InputOutputHelper.info("\nThe passkey has been deleted!")

    def change_pwd(self) -> None:
        """Change the name of the passkey or the passkey"""
        window = self.__get_title(list_titles=True)
        name = self.__get_name(window)

        if InputOutputHelper.ask_yes_no("Do you want to change the name?"):
            new_name = InputOutputHelper.ask_name()
        else:
            new_name = name

        if InputOutputHelper.ask_yes_no("Do you want to change the passkey?"):
            passkey = InputOutputHelper.ask_password(validate=True, ask_send_enter=True)

        del window.passkey_data[name]
        window.passkey_data[new_name] = passkey

        self.__save_config()
        self._set_password_required()
        InputOutputHelper.info("\nThe passkey has been updated successfully!")

    def list_titles(self, add_auto_complete: bool = True) -> None:
        """List all available title"""
        InputOutputHelper.title("\nAvailable titles are listed below: ")
        for window in self._config.windows:
            print(f" - {window.window_title}")
            if add_auto_complete:
                self._completer.add_new(window.window_title)

    def delete_title(self) -> None:
        """Delete a title"""
        window = self.__get_title()
        if window.passkey_data:
            if not InputOutputHelper.ask_yes_no(
                "There is at least one passkey found. Are you sure to delete this title with it's content?"
            ):
                raise ContinueLoopError()

        self._config.windows.remove(window)
        self.__save_config()
        InputOutputHelper.info(f"\nThe Title[{window.window_title}] has been deleted!")

    def change_mk(self) -> None:
        """Change the config file master key"""
        new_key = InputOutputHelper.ask_password(
            "Please enter the new Master Key",
            validate=True,
            ask_send_enter=False,
        ).encode(encoding=DFT_ENCODING)
        self._config_mgr.change_master_key(new_key)

        InputOutputHelper.info("\nThe Master Key has been changed!")

    def _set_password_required(self) -> None:
        """create the PASSWORD_REQUIRED_FILE_PATH file if password changed"""

        PASSWORD_REQUIRED_FILE_PATH.touch(exist_ok=True)

    def exit(self) -> None:
        """Exit the program"""
        self._is_active = False
        InputOutputHelper.warning("Exiting...")


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
    def ask_password(cls, prompt: str = "Please enter the new passkey", validate: bool = True, ask_send_enter: bool = False) -> str:
        """A standard way to get the passkey from the user"""
        passkey = getpass(f"{prompt}: ")
        if validate:
            passkey_validation = getpass(f"{prompt} again: ")

            if passkey != passkey_validation:
                cls.error("\nValues did not match!")
                raise ContinueLoopError

        if ASK_SEND_ENTER and ask_send_enter:
            if cls.ask_yes_no("Do you want to send the enter key after the password sent?"):
                passkey = passkey + "\n"
        else:
            passkey = passkey + "\n"
        return passkey

    @classmethod
    def title(cls, prompt: str) -> None:
        """A standard way to print an info message"""
        print(colorama.Fore.BLUE + prompt + colorama.Fore.RESET)

    @classmethod
    def info(cls, prompt: str) -> None:
        """A standard way to print an info message"""
        print(colorama.Fore.GREEN + prompt + colorama.Fore.RESET)

    @classmethod
    def warning(cls, prompt: str) -> None:
        """A standard way to print an warning message"""
        print(colorama.Fore.YELLOW + prompt + colorama.Fore.RESET)

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
        print(colorama.Fore.RED + prompt + colorama.Fore.RESET, file=sys.stderr)
        if exit_code is not None:
            sys.exit(exit_code)


class Completer:
    """Helper class for auto complete inputs"""

    def __init__(self) -> None:
        self._auto_complete: List[str] = []
        self._completer_setup()

    def _completer(self, text: str, state: int) -> str | None:
        options = [cmd for cmd in self._auto_complete if cmd.startswith(text)]
        if state < len(options):
            return options[state]
        return None

    def _completer_setup(self) -> None:
        # Workaround for readline error(AttributeError: module 'collections' has no attribute 'Callable')
        collections.Callable = collections.abc.Callable  # type: ignore[attr-defined]
        import readline  # pylint: disable=import-outside-toplevel

        readline.parse_and_bind("tab: complete")  # type: ignore[attr-defined]
        readline.set_completer(self._completer)  # type: ignore[attr-defined]

    def add_new(self, text: str) -> None:
        """Add a new item in the auto-complete list"""
        self._auto_complete.append(text)

    def clear(self) -> None:
        """Clear every item in the auto-complete list"""
        self._auto_complete.clear()


if __name__ == "__main__":
    main()

"""Helper functions for the updater."""

import enum
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
from functools import lru_cache as cache
from pathlib import Path
from types import TracebackType
from typing import Callable, Dict, Generator, List, Type

import requests

_UPDATE_LOOP_PREVENTION_ENV_VAR_NAME = "UPDATER_LOOP_PREVENTION"


def restart() -> None:
    """restart the application"""

    try:
        with subprocess.Popen(
            f"{sys.executable} {' '.join(sys.argv)}", env=os.environ | {_UPDATE_LOOP_PREVENTION_ENV_VAR_NAME: "1"}
        ) as process:
            pass
    except KeyboardInterrupt:
        pass
    sys.exit(process.returncode)


class NotifyType(enum.Enum):
    """Notification type."""

    DEBUG = enum.auto()
    INFO = enum.auto()
    QUESTION = enum.auto()
    ERROR = enum.auto()


def cli_user_notify_callback(message: str, kind: NotifyType) -> bool:
    """Default user notify callback function."""

    if kind in (NotifyType.DEBUG, NotifyType.INFO):
        print(message)
    elif kind == NotifyType.QUESTION:
        return input(f"{message} (y/N): ").strip() == "y"
    return True


class _NotificationManager:
    def __init__(self, user_notify_callback: Callable[[str, NotifyType], bool]) -> None:
        self.user_notify_callback = user_notify_callback

    @cache
    def notify(self, message: str, kind: NotifyType) -> bool:
        """Notify the user with the given message and kind."""
        return self.user_notify_callback(message, kind)

    def reserved(self) -> None:
        """Reserved for future use."""


class UpdateHelper:
    """Helper class for updating the application."""

    def __init__(
        self, raw_remote_url: str, hash_file_path: str, user_notify_callback: Callable[[str, NotifyType], bool] = cli_user_notify_callback
    ):
        self.raw_remote_url = raw_remote_url
        self.hash_file_path = hash_file_path
        self._update_list: List[str] | None = None
        self._downloaded_files: Dict[str, Path] = {}
        self._notification_manager = _NotificationManager(user_notify_callback)
        self._tempdir: Path | None = None

    def __enter__(self) -> "UpdateHelper":
        return self

    def __exit__(self, exc_type: Type[BaseException] | None, exc_inst: BaseException | None, exc_tb: TracebackType | None) -> None:
        self._cleanup()

    @staticmethod
    def md5(path: Path | str) -> str:
        """Generate the md5 hash of a file."""

        hash_md5 = hashlib.md5()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk.replace(b"\r", b""))
        return hash_md5.hexdigest()

    @staticmethod
    def download_single_file(url: str, path: Path) -> None:
        """Download a single file from the given URL."""

        response = requests.get(url, stream=True, timeout=100)
        response.raise_for_status()  # Ensure we got an OK response

        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

    @staticmethod
    def get_remote_hashes(hash_file_url: str) -> Dict[str, str]:
        """Return the hashes of the files on the remote server."""

        response = requests.get(hash_file_url, timeout=100)
        response.raise_for_status()  # Ensure we got an OK response

        hashes: List[str] = response.content.decode("utf-8").splitlines()

        hashes_dict = {}
        for hash_line in hashes:
            if not hash_line.strip() or not hash_line.startswith("H-"):
                continue

            md5_hash, path = hash_line.strip().split("H-")[1].split(" ", 1)
            hashes_dict[path] = md5_hash

        return hashes_dict

    @classmethod
    def get_update_list(cls, hash_file_url: str) -> Generator[str, None, None]:
        """Return the list of files that need to be updated."""

        remote_hashes = cls.get_remote_hashes(hash_file_url)

        for path, remote_hash in remote_hashes.items():
            try:
                local_hash = cls.md5(path)
            except FileNotFoundError:
                # it is a new file
                yield path
                continue

            if local_hash != remote_hash:
                yield path

    def _cleanup(self) -> None:
        if self._tempdir is not None:
            shutil.rmtree(self._tempdir)
            self._tempdir = None

    def check_for_updates(self, max_retries: int = 5, report_error: bool = True) -> bool | None:
        """Check for updates and notify the user if there are any."""

        for idx in range(max_retries):
            try:
                return self._check_for_updates()
            except (requests.exceptions.RequestException,) as e:
                if report_error:
                    raise e
                self._notification_manager.notify(f"Failed to check for updates. Retrying[{idx+1}/{max_retries}]", NotifyType.ERROR)

        self._notification_manager.notify("Failed to update... Please try again later.", NotifyType.ERROR)
        return False

    def _check_for_updates(self) -> bool | None:
        self._notification_manager.notify("Checking for updates...", NotifyType.INFO)

        if self._update_list is None:
            self._update_list = list(self.get_update_list(f"{self.raw_remote_url}/{self.hash_file_path}"))

        if not self._update_list:
            self._notification_manager.notify("No updates available.", NotifyType.INFO)
            return None

        if not self._notification_manager.notify("An update available. Do you want to update?", NotifyType.QUESTION):
            # User does not want to update
            self._notification_manager.notify("Update skipped.", NotifyType.INFO)
            return None

        if self._tempdir is None:
            self._tempdir = Path(tempfile.mkdtemp())

        self._notification_manager.notify("Downloading the new files, please wait...", NotifyType.INFO)

        for file in self._update_list[:]:
            file_replaced = file.replace("\\", "/")
            self._notification_manager.notify(f"downloading: {self.raw_remote_url}/{file_replaced}", NotifyType.DEBUG)

            temp_location = self._tempdir / file
            self.download_single_file(f"{self.raw_remote_url}/{file_replaced}", temp_location)

            self._update_list.remove(file)
            self._downloaded_files[file] = temp_location

        for file, temp_location in self._downloaded_files.items():
            self._notification_manager.notify(f"Replacing {file}...", NotifyType.DEBUG)
            Path(file).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(temp_location, file)
        self._notification_manager.notify("Updates downloaded successfully. Restarting the app.", NotifyType.INFO)

        return True


def check_for_updates(
    raw_remote_url: str,
    hash_file_path: str,
    user_notify_callback: Callable[[str, NotifyType], bool] = cli_user_notify_callback,
    max_retries: int = 5,
    report_error: bool = True,
) -> bool | None:
    """Check for updates and notify the user if there are any."""

    if os.getenv(_UPDATE_LOOP_PREVENTION_ENV_VAR_NAME, None) == "1":
        return None

    with UpdateHelper(raw_remote_url, hash_file_path, user_notify_callback) as updater:
        return updater.check_for_updates(max_retries, report_error)

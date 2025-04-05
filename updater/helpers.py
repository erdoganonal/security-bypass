"""Helper functions for the updater."""

import enum
import hashlib
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import Dict, Generator, List, Type

import requests

from common.tools import check_update_loop_guard_enabled
from handlers.notification.base import NotificationController
from logger import logger
from package_builder.registry import PBId, PBRegistry
from settings import RAW_REMOTE_URL, UPDATER_HASH_FILE

_SLEEP_SECS_BETWEEN_RETRIES = 10


class ModifyType(enum.Enum):
    """Modification type."""

    ADD = "A"
    REMOVE = "D"
    MODIFY = "M"


@dataclass
class ModifiedFile:
    """Modified file dataclass."""

    path: str
    kind: ModifyType


class UpdateHelper:
    """Helper class for updating the application."""

    def __init__(self) -> None:
        self._update_list: List[str] | None = None
        self._downloaded_files: Dict[str, Path] = {}
        self._tempdirs: Dict[str, Path] = {}
        self._notification_controller = PBRegistry.get_typed(PBId.NOTIFICATION_HANDLER, NotificationController)

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
            hashes_dict[md5_hash] = path

        return hashes_dict

    @classmethod
    def get_update_list(cls, hash_file_url: str) -> Generator[ModifiedFile, None, None]:
        """Return the list of files that need to be updated."""

        remote_hashes = cls.get_remote_hashes(hash_file_url)

        for remote_hash, path in remote_hashes.items():
            try:
                local_hash = cls.md5(path)
            except FileNotFoundError:
                # it is a new file
                yield ModifiedFile(path, ModifyType.ADD)
                continue

            if local_hash != remote_hash:
                yield ModifiedFile(path, ModifyType.MODIFY)

    def _cleanup(self) -> None:
        for tempdir in self._tempdirs.values():
            shutil.rmtree(tempdir)

        self._tempdirs = {}

    def check_for_updates(self, max_retries: int = 5, report_error: bool = True) -> bool | None:
        """Check for updates and notify the user if there are any."""

        for idx in range(max_retries):
            try:
                return self._check_for_updates()
            except OSError as e:
                if report_error:
                    raise e
                self._notification_controller.error(
                    f"Failed to check for updates. Will retry in {_SLEEP_SECS_BETWEEN_RETRIES} secs[{idx+1}/{max_retries}]"
                )
                time.sleep(_SLEEP_SECS_BETWEEN_RETRIES)

        self._notification_controller.error("Failed to update... Please try again later.")
        return False

    def _check_for_updates(self) -> bool | None:
        self._notification_controller.info("Checking for updates...")

        if self._update_list is None:
            self._update_list = [mod_file.path for mod_file in self.get_update_list(f"{RAW_REMOTE_URL}/{UPDATER_HASH_FILE}")]

        if not self._update_list:
            self._notification_controller.info("No updates available.")
            return None

        if not self._notification_controller.ask_yes_no("An update available. Do you want to update?"):
            # User does not want to update
            self._notification_controller.info("Update skipped.")
            return None

        try:
            download_temp_dir = self._tempdirs["download"]
        except KeyError:
            self._tempdirs["download"] = Path(tempfile.mkdtemp())
            download_temp_dir = self._tempdirs["download"]

        self._notification_controller.debug("Downloading the new files, please wait...")

        for file in self._update_list[:]:
            file_replaced = file.replace("\\", "/")
            self._notification_controller.debug(f"downloading: {RAW_REMOTE_URL}/{file_replaced}")

            temp_location = download_temp_dir / file
            self.download_single_file(f"{RAW_REMOTE_URL}/{file_replaced}", temp_location)

            self._backup(file)

            self._update_list.remove(file)
            self._downloaded_files[file] = temp_location

        try:
            return self._do_update()
        except OSError:
            self._do_rollback()
            raise

    def _backup(self, file: str) -> None:
        try:
            backup_temp_dir = self._tempdirs["backup"]
        except KeyError:
            self._tempdirs["backup"] = Path(tempfile.mkdtemp())
            backup_temp_dir = self._tempdirs["backup"]

        backup_temp_file = backup_temp_dir / file

        backup_temp_file.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(file, backup_temp_file)
        except FileNotFoundError:
            pass

    def _do_update(self) -> bool:
        temp_location = Path(tempfile.mktemp())

        for file, temp_location in self._downloaded_files.items():
            self._notification_controller.debug(f"Replacing {file}...")
            Path(file).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(temp_location, file)

        return self._complete_update()

    def _complete_update(self) -> bool:
        logger.debug("checking for changes in the requirements.txt file")

        for file in self._downloaded_files.values():
            if file.name == "requirements.txt":
                logger.info("requirements.txt file changed, going to install the new requirements")
                return self._install_requirements(file)

        return True

    def _install_requirements(self, file: Path) -> bool:
        try:
            out = subprocess.check_output(["pip", "install", "-r", str(file)], stderr=subprocess.STDOUT)
            logger.debug(out.decode("utf-8", errors="ignore"))

            self._notification_controller.info("Updates downloaded successfully. Restarting the app.")

            return True
        except subprocess.CalledProcessError:
            logger.exception("Failed to install requirements")

        return False

    def _do_rollback(self) -> None:
        try:
            backup_temp_dir = self._tempdirs["backup"]
        except KeyError:
            self._tempdirs["backup"] = Path(tempfile.mkdtemp())
            backup_temp_dir = self._tempdirs["backup"]

        for file in self._downloaded_files:
            try:
                shutil.copy2((backup_temp_dir / file), file)
            except FileNotFoundError:
                pass


def check_for_updates(
    max_retries: int = 5,
    report_error: bool = True,
    force_check: bool = False,
) -> bool | None:
    """Check for updates and notify the user if there are any."""

    if not force_check and check_update_loop_guard_enabled():
        return None

    with UpdateHelper() as updater:
        return updater.check_for_updates(max_retries, report_error)

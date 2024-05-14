"""creates an executable that extracts itself and runs a post-script"""

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from zipfile import ZipFile

import py7zr

CURRENT_DIR = Path(__file__).parent
TEMP_DATA_DIR = CURRENT_DIR / "tmp"
SFX_FILE = CURRENT_DIR / "7zSD.sfx"


@dataclass
class InstallerData:
    """Parameters for creating the installer"""

    name: Path
    config_file: Path
    post_script: Path
    zip_file: Path


class Installer:
    """helper methods/functions for creating an installer script"""

    @classmethod
    def create(cls, installer_data: InstallerData, files: Iterable[Path]) -> None:
        """combination of creating zip, executable and cleanup"""

        cls.create_zip(installer_data.zip_file, files)
        cls.create_executable(installer_data)
        cls.cleanup(installer_data)

    @classmethod
    def create_executable(cls, installer_data: InstallerData) -> None:
        """prepare the environment and create a self extracting executable"""

        cls.prepare_environment(installer_data)

        with open(installer_data.name, "wb") as output:
            # Iterate over the list of files and copy their contents to the output file
            for file_name in (SFX_FILE, installer_data.config_file, installer_data.zip_file):
                with open(file_name, "rb") as input_file:
                    shutil.copyfileobj(input_file, output)

    @classmethod
    def prepare_environment(cls, installer_data: InstallerData) -> None:
        """do initial environment preparation"""

        TEMP_DATA_DIR.mkdir(exist_ok=True)

        shutil.copy(installer_data.zip_file, TEMP_DATA_DIR)
        shutil.copy(installer_data.post_script, TEMP_DATA_DIR)
        shutil.copy(installer_data.config_file, TEMP_DATA_DIR)
        shutil.copy(SFX_FILE, TEMP_DATA_DIR)

        with py7zr.SevenZipFile(installer_data.zip_file, "w") as archive:
            archive.writeall(TEMP_DATA_DIR.relative_to(CURRENT_DIR))

    @classmethod
    def create_zip(cls, zip_filename: Path, files: Iterable[Path]) -> None:
        """add given files to a zip file"""

        with ZipFile(zip_filename, "w") as archive:
            for file in files:
                archive.write(file.absolute().relative_to(CURRENT_DIR))

    @classmethod
    def cleanup(cls, installer_data: InstallerData) -> None:
        """clean up temporary files"""

        shutil.rmtree(TEMP_DATA_DIR, ignore_errors=True)

        installer_data.zip_file.unlink(missing_ok=True)

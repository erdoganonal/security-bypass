"""creates a zip file for self extracting executable"""

from typing import Generator, Iterable, TypeVar

from common.tools import generate_wrapper_file
from exclusion.manager import get_files
from generate_all import main as generate_all
from installer import Installer, InstallerData
from settings import CURRENT_DIR, WRAPPER_FILE

INSTALLER_DIR = CURRENT_DIR / "installer"


CONFIG_FILE = INSTALLER_DIR / "Config.txt"
INSTALLER_SCRIPT = INSTALLER_DIR / "install.bat"
ZIP_APP_FILENAME = CURRENT_DIR / "windows_security_bypass.zip"
EXE_APP_FILENAME = CURRENT_DIR / "windows_security_bypass_installer.exe"


_T = TypeVar("_T")


ADDITIONAL = [
    WRAPPER_FILE,
]


def main() -> None:
    """starts from here"""
    generate_all()
    generate_wrapper_file()

    files = get_files()
    Installer.create(
        InstallerData(name=EXE_APP_FILENAME, config_file=CONFIG_FILE, post_script=INSTALLER_SCRIPT, zip_file=ZIP_APP_FILENAME),
        _extended(files, ADDITIONAL),
    )


def _extended(*iterables: Iterable[_T]) -> Generator[_T, None, None]:
    for it in iterables:
        yield from it


if __name__ == "__main__":
    try:
        main()
    finally:
        WRAPPER_FILE.unlink(missing_ok=True)

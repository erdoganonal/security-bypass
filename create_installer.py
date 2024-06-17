"""creates a zip file for self extracting executable"""

import fnmatch
import subprocess
import sys
from pathlib import Path
from typing import Generator, Iterable, TypeVar

from generate_all import main as generate_all
from installer import Installer, InstallerData
from updater.constants import UPDATER_FILE_NAME

CURRENT_DIR = Path(__file__).parent
INSTALLER_DIR = CURRENT_DIR / "installer"

WRAPPER_FILE = CURRENT_DIR / "security_bypass_wrapper.py"

CONFIG_FILE = INSTALLER_DIR / "Config.txt"
INSTALLER_SCRIPT = INSTALLER_DIR / "install.bat"
ZIP_APP_FILENAME = CURRENT_DIR / "windows_security_bypass.zip"
EXE_APP_FILENAME = CURRENT_DIR / "windows_security_bypass_installer.exe"


_T = TypeVar("_T")

EXCLUDED_FILES = [
    __file__,
    "*.bat",
    "*.txt",
    "*.toml",
    "*.zip",
    "*.sfx",
    UPDATER_FILE_NAME,
]

EXCLUDED_FOLDERS = [
    ".vscode",
    ".gitignore",
    "tests",
]

ADDITIONAL = [
    WRAPPER_FILE,
    CURRENT_DIR / "requirements.txt",
]


def main() -> None:
    """starts from here"""
    generate_all()
    generate_wrapper_file()

    files = get_files_to_archive()
    Installer.create(
        InstallerData(name=EXE_APP_FILENAME, config_file=CONFIG_FILE, post_script=INSTALLER_SCRIPT, zip_file=ZIP_APP_FILENAME),
        _extended(files, ADDITIONAL),
    )


def _extended(*iterables: Iterable[_T]) -> Generator[_T, None, None]:
    for it in iterables:
        yield from it


def _is_excluded(path: Path) -> bool:
    for excluded_file in EXCLUDED_FILES:
        if fnmatch.fnmatch(path.name, Path(excluded_file).name):
            return True

    return path.parts[0] in EXCLUDED_FOLDERS


def generate_wrapper_file() -> None:
    """generate the wrapper file"""

    content = '''"""wrapper for the main application to catch unhandled exceptions"""

try:
    import time
    import traceback
    from security_bypass import main

    main()
except Exception as e:
    traceback.print_exception(e)
    with open("error.log", "a+", encoding="utf-8") as error_fd:
        error_fd.write(f"{time.time()} - {e}\n")

    raise SystemExit(1) from e
'''

    with open(WRAPPER_FILE, "w", encoding="utf-8") as wrapper_fd:
        wrapper_fd.write(content)


def get_files_to_archive() -> Generator[Path, None, None]:
    """get list of all files to include in the zip file"""
    try:
        items = subprocess.check_output("git ls-tree -r main --name-only", text=True).splitlines()
    except subprocess.CalledProcessError:
        sys.exit("Error: Not a git repository or no files in the repository.")
    except FileNotFoundError:
        sys.exit("Error: Git is not installed.")

    for item in items:
        path = Path(item)
        if _is_excluded(path):
            continue
        yield path


if __name__ == "__main__":
    try:
        main()
    finally:
        WRAPPER_FILE.unlink(missing_ok=True)

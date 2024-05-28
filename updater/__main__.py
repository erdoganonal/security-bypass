"""This module is the entry point for the updater package."""

import argparse
import itertools
import subprocess
import sys
from functools import cache
from pathlib import Path
from typing import Iterable, List, Set

from updater.constants import UPDATER_FILE_NAME
from updater.helpers import get_update_list, md5

_GLOBALS = {
    "verbose": False,
}

_COMMAND_GENERATE_HASHES = "generate-hashes"
_COMMAND_SHOW_REMOTE = "show-remote"
_COMMAND_SHOW_UPDATE_LIST = "show-update-list"

_REMOTE_RAW_URL_CACHE_PATH = Path(".updater_remote_raw_url_cache")


def main() -> None:
    """start from here"""
    args = _parse_args()

    _GLOBALS["verbose"] = args.verbose

    if args.command == _COMMAND_GENERATE_HASHES:
        print("Generating hashes for the files...")
        generate_updater(_get_files(args.include, args.exclude))
        print("Hashes generated successfully.")
    elif args.command == _COMMAND_SHOW_REMOTE:
        print(_get_remote_raw_url())
    elif args.command == _COMMAND_SHOW_UPDATE_LIST:
        print("The following files either changed or added. It is need to be updated:\n")
        for file in get_update_list(args.hash_file_url + "/" + args.hash_file_name):
            print(file)
    else:
        print("Invalid command!")


@cache
def _get_remote_raw_url() -> str:
    if _REMOTE_RAW_URL_CACHE_PATH.exists():
        with open(_REMOTE_RAW_URL_CACHE_PATH, "r", encoding="utf-8") as cache_fd:
            return cache_fd.read()

    remote_url = subprocess.check_output("git remote get-url origin", text=True).strip()
    remote_name = subprocess.check_output("git remote", text=True).strip()
    default_branch = "main"
    for line in subprocess.check_output(f"git remote show {remote_name}", text=True).splitlines():
        if "HEAD branch" in line:
            default_branch = line.split(":")[1].strip()
            break

    *_, user, repo = remote_url.split("/")
    remote_raw_url = f"https://raw.github.com/{user}/{repo}/{default_branch}"
    with open(_REMOTE_RAW_URL_CACHE_PATH, "w", encoding="utf-8") as cache_fd:
        cache_fd.write(remote_raw_url)
    return remote_raw_url


def _get_files(include: List[str], exclude: List[str]) -> Set[Path]:
    current_list = subprocess.check_output("git ls-files", text=True).splitlines()
    _verbose_print(f"Current list of files: {current_list}")
    _verbose_print(f"Include files: {include}")
    _verbose_print(f"Exclude files: {exclude}")

    unique = set()
    for file in itertools.chain(current_list, include):
        unique.add(Path(file).resolve())

    return unique - set(Path(f).resolve() for f in exclude)


def _verbose_print(message: str = "") -> None:
    if _GLOBALS["verbose"]:
        print(message)


def generate_updater(paths: Iterable[Path]) -> None:
    """generates hashes for the files"""

    top_level = Path(subprocess.check_output("git rev-parse --show-toplevel", text=True).strip())

    hashes = "generated by updater with following command:\npython -m updater " + " ".join(sys.argv[1:]) + "\n\n"
    for path in sorted(paths):
        md5_hash = md5(path)
        _verbose_print(f"Hash for {path.relative_to(top_level)}: {md5_hash}")
        hashes += md5_hash + " " + str(path.relative_to(top_level)) + "\n"

    _verbose_print()

    with open(UPDATER_FILE_NAME, "w", encoding="utf-8") as hashes_fd:
        hashes_fd.write(hashes)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")
    generate_parser = subparsers.add_parser(_COMMAND_GENERATE_HASHES)
    generate_parser.add_argument("-i", "--include", default=[], nargs=argparse.ONE_OR_MORE, help="file to generate hashes for")
    generate_parser.add_argument("-e", "--exclude", default=[], nargs=argparse.ONE_OR_MORE, help="file to exclude from generating hashes")

    subparsers.add_parser(_COMMAND_SHOW_REMOTE)

    show_update_parser = subparsers.add_parser(_COMMAND_SHOW_UPDATE_LIST)
    show_update_parser.add_argument("hash_file_url", help="URL of the hash file")
    show_update_parser.add_argument("hash_file_name", help="Name of the hash file")

    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")

    return parser.parse_args()


if __name__ == "__main__":
    main()

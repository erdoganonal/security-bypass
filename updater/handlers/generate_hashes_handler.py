"""This module contains the handler for the generate-hashes command."""

import argparse
import itertools
import json
import subprocess
import sys
from functools import cache
from pathlib import Path
from typing import Iterable, List, Set, TypedDict

from updater.constants import UPDATER_FILE_NAME
from updater.handlers.common import error, verbose
from updater.helpers import UpdateHelper

_UPDATER_OPTIONS_FILE = Path(".updater_options")


class Options(TypedDict):
    """Options for the updater."""

    include: List[str]
    exclude: List[str]


def handle_generate_hashes(args: argparse.Namespace) -> None:
    """Handles the generate-hashes command."""

    if args.save:
        _save_options(args)
    elif args.show:
        _show_options()
    elif args.delete:
        _delete_options()
    elif not args.ignore_saved:
        _extend_args_with_options(args)

    print("Generating hashes for the files...")
    generate_updater(_get_files(args.include, args.exclude))
    print("Hashes generated successfully.")


def _save_options(args: argparse.Namespace) -> None:
    print("Saving options...")
    options = {
        "include": args.include,
        "exclude": args.exclude,
    }
    options_as_str = json.dumps(options)
    with open(_UPDATER_OPTIONS_FILE, "w", encoding="utf-8") as options_fd:
        options_fd.write(options_as_str)
    print("Options saved successfully.\n")


@cache
def load_options() -> Options:
    """Load the saved options."""

    try:
        with open(_UPDATER_OPTIONS_FILE, "r", encoding="utf-8") as options_fd:
            return json.load(options_fd)  # type: ignore[no-any-return]
    except FileNotFoundError:
        return {"include": [], "exclude": []}


def _show_options() -> None:
    if not _UPDATER_OPTIONS_FILE.exists():
        print("No saved options found.")
        sys.exit(0)

    options = load_options()

    print("Saved options:")
    print(f"Include: {options['include']}")
    print(f"Exclude: {options['exclude']}")
    print("\nOptions as a command line:")
    if options["include"]:
        print(f"--include {' '.join(options['include'])}", end=" ")
    if options["exclude"]:
        print(f"--exclude {' '.join(options['exclude'])}", end=" ")
    print()
    sys.exit(0)


def _delete_options() -> None:
    print("Deleting saved options...")
    _UPDATER_OPTIONS_FILE.unlink()
    print("Options deleted successfully.")
    sys.exit(0)


def _extend_args_with_options(args: argparse.Namespace) -> None:
    options = load_options()

    args.include.extend(options["include"])
    args.exclude.extend(options["exclude"])


def _get_files(include: List[str], exclude: List[str]) -> Set[Path]:
    try:
        current_list = subprocess.check_output("git ls-files", text=True).splitlines()
    except subprocess.CalledProcessError:
        error("Not a git repository or no files in the repository.")
    except FileNotFoundError:
        error("Git is not installed.")

    verbose(f"Current list of files: {current_list}")
    verbose(f"Include files: {include}")
    verbose(f"Exclude files: {exclude}")

    unique = set()
    for file in itertools.chain(current_list, include):
        unique.add(Path(file).resolve())

    return unique - set(Path(f).resolve() for f in exclude)


def generate_updater(paths: Iterable[Path]) -> None:
    """generates hashes for the files"""

    top_level = Path(subprocess.check_output("git rev-parse --show-toplevel", text=True).strip())

    hashes = "generated by updater with following command:\npython -m updater " + " ".join(sys.argv[1:]) + "\n"
    options = load_options()
    if options["include"] or options["exclude"]:
        hashes += "With the following saved options:\n"
        hashes += f"Include: {options['include']}\n"
        hashes += f"Exclude: {options['exclude']}\n\n"
    else:
        hashes += "Without any saved options.\n\n"
    for path in sorted(paths):
        md5_hash = UpdateHelper.md5(path)
        verbose(f"Hash for {path.relative_to(top_level)}: {md5_hash}")
        hashes += "H-" + md5_hash + " " + str(path.relative_to(top_level)) + "\n"

    verbose()

    with open(UPDATER_FILE_NAME, "w", encoding="utf-8") as hashes_fd:
        hashes_fd.write(hashes)

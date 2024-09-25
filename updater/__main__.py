"""This module is the entry point for the updater package."""

import argparse

from updater.handlers.common import GLOBALS, get_remote_raw_url
from updater.handlers.generate_hashes_handler import handle_generate_hashes
from updater.helpers import UpdateHelper

_COMMAND_GENERATE_HASHES = "generate-hashes"
_COMMAND_SHOW_REMOTE = "show-remote"
_COMMAND_SHOW_UPDATE_LIST = "show-update-list"


def main() -> None:
    """start from here"""
    args = _parse_args()

    GLOBALS["verbose"] = args.verbose

    if args.command == _COMMAND_GENERATE_HASHES:
        handle_generate_hashes(args)
    elif args.command == _COMMAND_SHOW_REMOTE:
        print(get_remote_raw_url())
    elif args.command == _COMMAND_SHOW_UPDATE_LIST:
        print("The following files either changed or added. It is need to be updated:\n")
        for file in UpdateHelper.get_update_list(args.hash_file_url + "/" + args.hash_file_name):
            print(file)
    else:
        print("Invalid command!")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(dest="command")
    generate_parser = subparsers.add_parser(_COMMAND_GENERATE_HASHES)
    generate_parser.add_argument("-i", "--include", default=[], nargs=argparse.ONE_OR_MORE, help="file to generate hashes for")
    generate_parser.add_argument("-e", "--exclude", default=[], nargs=argparse.ONE_OR_MORE, help="file to exclude from generating hashes")

    generate_parser.add_argument("-s", "--save", action="store_true", help="saved passed options to a file")
    generate_parser.add_argument("-S", "--show", action="store_true", help="show the saved options")
    generate_parser.add_argument("-d", "--delete", action="store_true", help="delete the saved options")
    generate_parser.add_argument("-I", "--ignore-saved", action="store_true", help="ignore the saved options")

    subparsers.add_parser(_COMMAND_SHOW_REMOTE)

    show_update_parser = subparsers.add_parser(_COMMAND_SHOW_UPDATE_LIST)
    show_update_parser.add_argument("-n", "--hash-file-name", help="Name of the hash file", required=True)
    show_update_parser.add_argument("-u", "--hash-file-url", help="URL of the hash file", default=get_remote_raw_url())

    parser.add_argument("-v", "--verbose", action="store_true", help="increase output verbosity")

    return parser.parse_args()


if __name__ == "__main__":
    main()

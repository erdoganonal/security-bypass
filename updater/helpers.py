"""Helper functions for the updater."""

import hashlib
from pathlib import Path
from typing import Dict, Generator, List

import requests


def md5(path: Path | str) -> str:
    """Generate the md5 hash of a file."""

    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_remote_hashes(hash_file_url: str) -> Dict[str, str]:
    """Return the hashes of the files on the remote server."""

    response = requests.get(hash_file_url, timeout=100)
    response.raise_for_status()  # Ensure we got an OK response

    hashes: List[str] = response.content.decode("utf-8").splitlines()

    hashes_dict = {}
    for hash_line in hashes[2:]:
        if not hash_line.strip():
            continue

        md5_hash, path = hash_line.strip().split(" ", 1)
        hashes_dict[path] = md5_hash

    return hashes_dict


def get_update_list(hash_file_url: str) -> Generator[str, None, None]:
    """Return the list of files that need to be updated."""

    remote_hashes = get_remote_hashes(hash_file_url)

    for path, remote_hash in remote_hashes.items():
        try:
            local_hash = md5(path)
        except FileNotFoundError:
            # it is a new file
            yield path
            continue

        if local_hash != remote_hash:
            yield path

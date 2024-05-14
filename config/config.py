"""Parse the config file and get the pre-saved passwords"""


import json
import os
import re
from builtins import bytes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Literal, TypeAlias, overload

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256

from settings import CONFIG_PATH, CREDENTIALS_FILE, DFT_ENCODING

T: Dict[str, Dict[str, str]] = {
    "Windows Security": {
        "PIN": "00393200\n",
        "PinkyPwd": "apple/pear_2022#1\n",
    },
}

ConfigDict: TypeAlias = Dict[str, Dict[str, str]]


@dataclass
class WindowConfig:
    """Window title/passkey data pairs"""

    window_title: str
    passkey_data: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.pattern = re.compile(self.window_title)


@dataclass
class Config:
    """Group of WindowConfig's"""

    windows: List[WindowConfig]

    def to_dict(self) -> ConfigDict:
        """Convert Config object to dictionary"""
        return {window.window_title: window.passkey_data for window in self.windows}

    @classmethod
    def from_dict(cls, data: ConfigDict) -> "Config":
        """Convert dictionary to Config object"""
        return cls([WindowConfig(window_title, passkey_data) for window_title, passkey_data in data.items()])

    @overload
    def to_json(self, encode: Literal[True]) -> bytes:
        ...

    @overload
    def to_json(self, encode: Literal[False]) -> str:
        ...

    def to_json(self, encode: bool = False) -> str | bytes:
        """Convert the Config object to a json string or bytes"""

        data = json.dumps(self.to_dict())
        if encode:
            return data.encode(DFT_ENCODING)
        return data

    @classmethod
    def from_json(cls, data: str | bytes) -> "Config":
        """Convert JSON str/bytes to Config object"""
        return cls.from_dict(json.loads(data))

    def to_user_str(self) -> str:
        """Print the config as human readable form"""
        res = ""

        for window in self.windows:
            res += f"Title: {window.window_title}\n"
            for name, key in window.passkey_data.items():
                res += f" - {name}: {key.strip()}\n"

        return res.strip()


class ConfigManager:
    """Helps to load/save the configuration in a secure way."""

    def __init__(self, key: bytes) -> None:
        self.__key = key

    def get_config(self) -> Config:
        """Load and decrypt the passkey data in the config file"""

        cfg_data = self.decrypt_file(CREDENTIALS_FILE)
        return Config.from_json(cfg_data)

    def save_config(self, cfg: Config) -> None:
        """Save the passkey data in the config file encrypted"""
        os.makedirs(CONFIG_PATH, exist_ok=True)

        self.encrypt_file(CREDENTIALS_FILE, cfg.to_json(True))

    def decrypt_file(self, filename: str | Path) -> bytes:
        """Open given file and decrypt it's content using the Master Key"""

        with open(filename, "rb") as fd:
            return self.decrypt(fd.read())

    def encrypt_file(self, filename: str | Path, data: bytes) -> None:
        """Encrypt the given data using Master Key and write it to the given file"""

        with open(filename, "wb") as fd:
            fd.write(self.encrypt(data))

    def encrypt(self, source: bytes) -> bytes:
        """Encrypt given source using Master Key"""

        key = SHA256.new(self.__key).digest()  # use SHA-256 over our key to get a proper-sized AES key
        iv = Random.new().read(AES.block_size)  # generate IV
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        padding = AES.block_size - len(source) % AES.block_size  # calculate needed padding
        source += bytes([padding]) * padding  # Python 2.x: source += chr(padding) * padding
        data = iv + encryptor.encrypt(source)  # store the IV at the beginning and encrypt

        return data

    def decrypt(self, source: bytes) -> bytes:
        """Decrypt given source using Master Key"""

        key = SHA256.new(self.__key).digest()  # use SHA-256 over our key to get a proper-sized AES key
        iv = source[: AES.block_size]  # extract the IV from the beginning
        decryptor = AES.new(key, AES.MODE_CBC, iv)
        data = decryptor.decrypt(source[AES.block_size :])  # decrypt
        padding = data[-1]  # pick the padding value from the end; Python 2.x: ord(data[-1])
        if data[-padding:] != bytes([padding]) * padding:  # Python 2.x: chr(padding) * padding
            raise ValueError("Invalid padding...")

        return data[:-padding]  # remove the padding

    def change_master_key(self, new_key: bytes, filename: str | Path = CREDENTIALS_FILE) -> None:
        """Changes the master key with given key"""
        file_content = self.decrypt_file(filename)
        self.__key = new_key
        self.encrypt_file(filename, file_content)

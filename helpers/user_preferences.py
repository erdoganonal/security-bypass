"""Module for managing configuration files."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from handlers.authentication.methods import AuthMethod
from settings import USER_PREFERENCES_FILE


@dataclass
class UserPreferences:
    """UserPreferences data class."""

    auto_start: bool = True
    auto_update: bool = True
    repeated_window_protection: bool = True
    auth_method: AuthMethod = AuthMethod.PASSWORD

    def to_dict(self) -> dict[str, Any]:
        """Convert the data to a dictionary."""
        return {
            "auto_start": self.auto_start,
            "auto_update": self.auto_update,
            "repeated_window_protection": self.repeated_window_protection,
            "auth_method": self.auth_method.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UserPreferences":
        """Create an instance from a dictionary."""
        return cls(
            auto_start=data["auto_start"],
            auto_update=data["auto_update"],
            repeated_window_protection=data.get("repeated_window_protection", True),
            auth_method=AuthMethod(data.get("auth_method", AuthMethod.PASSWORD.value)),
        )


class UserPreferencesAccessor:
    """Accessor for configuration files."""

    _USER_PREFERENCES: UserPreferences | None = None

    @staticmethod
    def save(file_path: str | Path, data: UserPreferences) -> None:
        """
        Save data to a JSON file.

        :param file_path: Path to the JSON file.
        :param data: Data to be saved.
        """
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data.to_dict(), f, indent=4)

    @classmethod
    def partial_save(cls, file_path: str | Path, **kwargs: Any) -> None:
        """
        Partially save data to a JSON file.

        :param file_path: Path to the JSON file.
        :param kwargs: Data to be saved.
        """
        config = cls.load(file_path)
        for key, value in kwargs.items():
            setattr(config, key, value)
        cls.save(file_path, config)

    @classmethod
    def load(cls, file_path: str | Path = USER_PREFERENCES_FILE) -> UserPreferences:
        """
        Load data from a JSON file.

        :param file_path: Path to the JSON file.
        :return: Data loaded from the file.
        """

        if not Path(file_path).exists():
            cls._USER_PREFERENCES = UserPreferences()
            return cls._USER_PREFERENCES

        with open(file_path, "r", encoding="utf-8") as f:
            config_dict = json.load(f)

        cls._USER_PREFERENCES = UserPreferences.from_dict(config_dict)
        return cls._USER_PREFERENCES

    @classmethod
    def get(cls, force_reload: bool = False) -> UserPreferences:
        """Get the configuration data."""
        if cls._USER_PREFERENCES is None or force_reload:
            return cls.load()

        return cls._USER_PREFERENCES

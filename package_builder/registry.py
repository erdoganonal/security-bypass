"""Registry to store the items in the package builder."""

import enum
from typing import Any, Type, TypeVar

T = TypeVar("T")


class PBId(enum.Enum):
    """ID of the items in the package builder."""

    NOTIFICATION_HANDLER = enum.auto()
    SELECT_WINDOW = enum.auto()
    AUTHENTICATION_HANDLER = enum.auto()


class PBRegistry:
    """Package Builder class to store the items in the package builder.
    Helps to avoid using singletons and global variables.
    """

    _registry: dict[PBId, Any] = {}

    @classmethod
    def register(cls, pb_id: PBId, value: Any) -> None:
        """Register the value with the id."""

        if cls._registry.get(pb_id):
            raise KeyError(f"PBId {pb_id} already exists in the registry.")

        cls._registry[pb_id] = value

    @classmethod
    def get(cls, pb_id: PBId) -> Any:
        """Get the value with the id."""

        return cls._registry[pb_id]

    @classmethod
    def get_typed(cls, pb_id: PBId, type_: Type[T]) -> T:  # pylint: disable=unused-argument
        """Get the value with the id and cast it to the type."""

        return cls._registry[pb_id]  # type: ignore[no-any-return]

    @classmethod
    def unregister(cls, pb_id: PBId) -> None:
        """Unregister the value with the id."""

        del cls._registry[pb_id]

    @classmethod
    def check_all_registered(cls) -> None:
        """Check if all the items are registered."""

        for pb_id in PBId:
            if pb_id not in cls._registry:
                raise KeyError(f"All the items are not registered in the package builder: {pb_id}.")

    @classmethod
    def register_safe(cls, pb_id: PBId, value: Any) -> None:
        """Register the value with given package builder id.
        If the id is already registered, ignore it.
        """

        try:
            cls.register(pb_id, value)
        except KeyError:
            pass

    @classmethod
    def register_override(cls, pb_id: PBId, value: Any) -> None:
        """Register the value with given package builder id.
        If the id is already registered, override it.
        """

        try:
            cls.unregister(pb_id)
        except KeyError:
            pass
        cls.register(pb_id, value)

from enum import Enum
from typing import Optional
from typing import TypeVar

T = TypeVar("T", bound="GardenEnum")


class GardenEnum(Enum):
    """
    Why use an Enum?
    - Type safety: Ensures only valid frame types are used
    - Readability: Self-documenting code with clear intent
    - IDE support: Better autocompletion and refactoring

    Performance note:
    - Enum lookup is O(1) and very efficient
    - Enums are singletons, so memory footprint is minimal
    - Prefer identity checks (is) over equality (==) for best performance
    """

    @classmethod
    def from_string(cls: type[T], value: str) -> Optional[T]:
        """
        Get a Subclass Enum member from a string value (case-insensitive).

        Args:
            value (str): The value to look up, case-insensitive.

        Returns:
            The enum member with a matching value, or None if no match is found.

        Example:
            >>> Subclass.from_string("unknow_cmd")
            <Subclass.UNKNOW_CMD: 'UNKNOW_CMD'>

            >>> Subclass.from_string("INVALID_param")
            <Subclass.INVALID_PARAM: 'INVALID_PARAM'>

            >>> Subclass.from_string("nonexistent")
            None
        """
        value = value.upper()
        for member in cls:
            if member.value == value:
                return member
        return None

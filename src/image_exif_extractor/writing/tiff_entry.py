from __future__ import annotations

from dataclasses import dataclass
from typing import Final

VALUE_FIELD_SIZE: Final[int] = 4


@dataclass(frozen=True)
class TiffEntry:
    """
    One 12-byte entry of an image file directory, as stored.

    The value field holds the value itself when it fits in four bytes, and otherwise
    the offset of the value from the start of the TIFF header. Entries copied from
    an existing directory keep their value field unchanged, so values stored
    elsewhere in the block stay where they are.

    Attributes
    ----------
    tag
        The tag id.
    field_type
        The TIFF field type code, kept as stored even when not a `TiffFieldType`.
    count
        The number of values.
    value_field
        The four bytes of the value or of its offset, in the block's byte order.

    Raises
    ------
    ValueError
        If `value_field` is not four bytes long or a number is out of range.
    """

    tag: int
    field_type: int
    count: int
    value_field: bytes

    def __post_init__(self) -> None:
        if len(self.value_field) != VALUE_FIELD_SIZE:
            raise ValueError(f"value_field must be 4 bytes, given: {len(self.value_field)}")
        if not 0 <= self.tag <= 0xFFFF or not 0 <= self.field_type <= 0xFFFF:
            raise ValueError(f"Invalid tag {self.tag} or field type {self.field_type}")
        if not 0 <= self.count <= 0xFFFFFFFF:
            raise ValueError(f"Invalid count: {self.count}")

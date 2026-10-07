from __future__ import annotations

from enum import Enum


class ByteOrder(Enum):
    """
    The byte order a TIFF block is written in, named by its first two bytes.

    Attributes
    ----------
    BIG_ENDIAN
        `MM`, most significant byte first, as most cameras write.
    LITTLE_ENDIAN
        `II`, least significant byte first.
    """

    BIG_ENDIAN = b"MM"
    LITTLE_ENDIAN = b"II"

    @property
    def struct_prefix(self) -> str:
        """
        Return the `struct` format prefix of the byte order.

        Returns
        -------
        str
            `>` or `<`.
        """
        match self:
            case ByteOrder.BIG_ENDIAN:
                return ">"
            case ByteOrder.LITTLE_ENDIAN:
                return "<"

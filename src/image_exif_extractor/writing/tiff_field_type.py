from __future__ import annotations

from enum import IntEnum


class TiffFieldType(IntEnum):
    """
    The TIFF field types written when tags are set.

    Attributes
    ----------
    BYTE
        8-bit unsigned integers.
    ASCII
        NUL-terminated 7-bit text.
    SHORT
        16-bit unsigned integers.
    LONG
        32-bit unsigned integers, as directory pointers are.
    RATIONAL
        Pairs of 32-bit unsigned integers, numerator then denominator.
    """

    BYTE = 1
    ASCII = 2
    SHORT = 3
    LONG = 4
    RATIONAL = 5

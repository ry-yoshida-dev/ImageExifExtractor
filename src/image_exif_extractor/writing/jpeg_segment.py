from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Final

MARKER_PREFIX: Final[int] = 0xFF
APP1_MARKER: Final[int] = 0xE1
EXIF_SIGNATURE: Final[bytes] = b"Exif\x00\x00"
MAXIMUM_PAYLOAD: Final[int] = 0xFFFF - 2
STANDALONE_MARKERS: Final[frozenset[int]] = frozenset({0x01, *range(0xD0, 0xD8)})


@dataclass(frozen=True)
class JpegSegment:
    """
    One marker segment of the header of a JPEG file.

    Attributes
    ----------
    marker
        The marker code after `0xFF`, such as `0xE1` for APP1.
    payload
        The bytes after the length field, empty for standalone markers.

    Raises
    ------
    ValueError
        If the payload does not fit in a segment.
    """

    marker: int
    payload: bytes

    def __post_init__(self) -> None:
        if len(self.payload) > MAXIMUM_PAYLOAD:
            raise ValueError(
                f"Segment payload of {len(self.payload)} bytes exceeds {MAXIMUM_PAYLOAD}"
            )

    @classmethod
    def exif(cls, tiff: bytes) -> JpegSegment:
        """
        Build the APP1 segment of an Exif block.

        Parameters
        ----------
        tiff : bytes
            The TIFF block of Exif, without signature.

        Returns
        -------
        JpegSegment
            The segment.

        Raises
        ------
        ValueError
            If the block does not fit in one segment of 64 KB.
        """
        return cls(marker=APP1_MARKER, payload=EXIF_SIGNATURE + tiff)

    @property
    def is_exif(self) -> bool:
        """
        Whether the segment holds an Exif block.

        Returns
        -------
        bool
            True for an APP1 segment starting with the Exif signature.
        """
        return self.marker == APP1_MARKER and self.payload.startswith(EXIF_SIGNATURE)

    @property
    def exif_tiff(self) -> bytes:
        """
        Return the TIFF block of an Exif segment.

        Returns
        -------
        bytes
            The payload after the Exif signature.

        Raises
        ------
        ValueError
            If the segment holds no Exif block.
        """
        if not self.is_exif:
            raise ValueError("Segment holds no Exif block")
        return self.payload[len(EXIF_SIGNATURE) :]

    def to_bytes(self) -> bytes:
        """
        Write the segment as stored in a file.

        Returns
        -------
        bytes
            The marker, the length field unless standalone, and the payload.
        """
        if self.marker in STANDALONE_MARKERS:
            return bytes((MARKER_PREFIX, self.marker))
        return (
            bytes((MARKER_PREFIX, self.marker))
            + struct.pack(">H", len(self.payload) + 2)
            + (self.payload)
        )

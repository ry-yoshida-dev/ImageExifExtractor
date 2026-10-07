from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Final

from .jpeg_segment import MARKER_PREFIX, STANDALONE_MARKERS, JpegSegment

START_OF_IMAGE: Final[bytes] = b"\xff\xd8"
START_OF_SCAN_MARKER: Final[int] = 0xDA
END_OF_IMAGE_MARKER: Final[int] = 0xD9
APP0_MARKER: Final[int] = 0xE0


@dataclass(frozen=True)
class JpegFile:
    """
    A JPEG file split into its header segments and its compressed image data.

    Only the segments before the first scan are parsed. Everything from the start of
    scan on, the compressed pixels and anything appended after them, such as the
    second image of an MPO, is kept byte for byte, so replacing a header segment
    never re-encodes the image.

    Attributes
    ----------
    segments
        The marker segments between the start of image and the first scan.
    image_data
        The bytes from the start-of-scan marker to the end of the file.
    """

    segments: tuple[JpegSegment, ...]
    image_data: bytes

    @classmethod
    def parse(cls, data: bytes) -> JpegFile:
        """
        Split the bytes of a JPEG file.

        Parameters
        ----------
        data : bytes
            The file.

        Returns
        -------
        JpegFile
            Its segments and image data.

        Raises
        ------
        ValueError
            If the data is not a JPEG file or is truncated.
        """
        if not data.startswith(START_OF_IMAGE):
            raise ValueError("Not a JPEG file")
        segments: list[JpegSegment] = []
        position = len(START_OF_IMAGE)
        while True:
            if position + 2 > len(data) or data[position] != MARKER_PREFIX:
                raise ValueError(f"Expected a JPEG marker at byte {position}")
            while position + 1 < len(data) and data[position + 1] == MARKER_PREFIX:
                position += 1
            marker = data[position + 1]
            if marker == START_OF_SCAN_MARKER:
                return cls(segments=tuple(segments), image_data=data[position:])
            if marker == END_OF_IMAGE_MARKER:
                raise ValueError("JPEG file ends before any image data")
            if marker in STANDALONE_MARKERS:
                segments.append(JpegSegment(marker=marker, payload=b""))
                position += 2
                continue
            if position + 4 > len(data):
                raise ValueError("JPEG file is truncated")
            length: int = struct.unpack_from(">H", data, position + 2)[0]
            end = position + 2 + length
            if length < 2 or end > len(data):
                raise ValueError(f"Invalid segment length at byte {position}")
            segments.append(JpegSegment(marker=marker, payload=data[position + 4 : end]))
            position = end

    @property
    def exif_tiff(self) -> bytes | None:
        """
        Return the TIFF block of the first Exif segment.

        Returns
        -------
        bytes | None
            The block, or None when the file holds no Exif segment.
        """
        segment = next((segment for segment in self.segments if segment.is_exif), None)
        return None if segment is None else segment.exif_tiff

    def with_exif_tiff(self, tiff: bytes) -> JpegFile:
        """
        Replace the Exif block, or add one after the JFIF segment when there is none.

        Parameters
        ----------
        tiff : bytes
            The new TIFF block of Exif.

        Returns
        -------
        JpegFile
            The file with the block, every other segment and the image data unchanged.

        Raises
        ------
        ValueError
            If the block does not fit in one segment of 64 KB.
        """
        exif = JpegSegment.exif(tiff)
        segments = list(self.segments)
        index = next((index for index, segment in enumerate(segments) if segment.is_exif), None)
        if index is None:
            insert_at = next(
                (index for index, segment in enumerate(segments) if segment.marker != APP0_MARKER),
                len(segments),
            )
            segments.insert(insert_at, exif)
        else:
            segments[index] = exif
        return JpegFile(segments=tuple(segments), image_data=self.image_data)

    def to_bytes(self) -> bytes:
        """
        Write the file.

        Returns
        -------
        bytes
            The start of image, the segments and the image data.
        """
        return (
            START_OF_IMAGE
            + b"".join(segment.to_bytes() for segment in self.segments)
            + (self.image_data)
        )

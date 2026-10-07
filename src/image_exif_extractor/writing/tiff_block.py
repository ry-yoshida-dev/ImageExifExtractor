from __future__ import annotations

import struct
from typing import Final

from .byte_order import ByteOrder
from .tiff_directory import TiffDirectory
from .tiff_entry import VALUE_FIELD_SIZE, TiffEntry
from .tiff_field_type import TiffFieldType

HEADER_SIZE: Final[int] = 8
TIFF_MAGIC: Final[int] = 42
ENTRY_SIZE: Final[int] = 12
WORD_SIZE: Final[int] = 2
IFD0_OFFSET_POSITION: Final[int] = 4
MAXIMUM_OFFSET: Final[int] = 0xFFFFFFFF


class TiffBlock:
    """
    The TIFF structure an Exif block is written in, edited by appending.

    Directories are never rewritten in place. A changed directory is appended at the
    end of the block and the pointer to it updated, so every value stored elsewhere,
    such as the maker note, the thumbnail and the values of other tags, keeps its
    offset and stays valid. The space of the replaced directory is left unused.

    Parameters
    ----------
    data : bytes
        The block, starting with its `MM` or `II` header.

    Raises
    ------
    ValueError
        If the header is not a TIFF header.
    """

    def __init__(self, data: bytes) -> None:
        if len(data) < HEADER_SIZE:
            raise ValueError("TIFF block is shorter than its header")
        try:
            byte_order = ByteOrder(data[:2])
        except ValueError as error:
            raise ValueError(f"Invalid TIFF byte order: {data[:2]!r}") from error
        self._byte_order: ByteOrder = byte_order
        self._data: bytearray = bytearray(data)
        if self._unpack("H", 2) != TIFF_MAGIC:
            raise ValueError("Invalid TIFF header")

    @classmethod
    def empty(cls, byte_order: ByteOrder = ByteOrder.BIG_ENDIAN) -> TiffBlock:
        """
        Create a block holding an empty IFD0.

        Parameters
        ----------
        byte_order : ByteOrder
            The byte order to write in.

        Returns
        -------
        TiffBlock
            A header followed by a directory of no entry.
        """
        prefix = byte_order.struct_prefix
        header = byte_order.value + struct.pack(f"{prefix}HI", TIFF_MAGIC, HEADER_SIZE)
        return cls(header + struct.pack(f"{prefix}HI", 0, 0))

    @property
    def byte_order(self) -> ByteOrder:
        """
        Return the byte order of the block.

        Returns
        -------
        ByteOrder
            The order given by the header.
        """
        return self._byte_order

    @property
    def ifd0_offset(self) -> int:
        """
        Return the offset of IFD0, the directory of the main image.

        Returns
        -------
        int
            The offset from the start of the header.
        """
        return self._unpack("I", IFD0_OFFSET_POSITION)

    def read_directory(self, offset: int) -> TiffDirectory:
        """
        Read the directory at an offset.

        Parameters
        ----------
        offset : int
            The offset from the start of the header.

        Returns
        -------
        TiffDirectory
            Its entries, sorted by tag, and the offset of the next directory.

        Raises
        ------
        ValueError
            If the directory runs past the end of the block.
        """
        count = self._unpack("H", offset)
        end = offset + 2 + count * ENTRY_SIZE + 4
        if end > len(self._data):
            raise ValueError(f"Directory at {offset} runs past the end of the block")
        entries = [self._read_entry(offset + 2 + index * ENTRY_SIZE) for index in range(count)]
        unique = {entry.tag: entry for entry in entries}
        return TiffDirectory(
            entries=tuple(sorted(unique.values(), key=lambda entry: entry.tag)),
            next_offset=self._unpack("I", end - 4),
        )

    def pointer_of(self, directory: TiffDirectory, tag: int) -> int | None:
        """
        Read the offset a pointer tag of a directory holds.

        Parameters
        ----------
        directory : TiffDirectory
            The directory holding the pointer.
        tag : int
            The pointer tag, such as `ExifOffset` or `GPSInfo`.

        Returns
        -------
        int | None
            The offset of the directory pointed to, or None when the tag is absent.
        """
        entry = directory.find(tag)
        if entry is None:
            return None
        offset: int = struct.unpack(f"{self._byte_order.struct_prefix}I", entry.value_field)[0]
        return offset

    def append_directory(self, directory: TiffDirectory) -> int:
        """
        Write a directory at the end of the block.

        Parameters
        ----------
        directory : TiffDirectory
            The directory to write.

        Returns
        -------
        int
            Its offset, to point to it from its parent or the header.
        """
        prefix = self._byte_order.struct_prefix
        offset = self._align()
        self._data += struct.pack(f"{prefix}H", len(directory.entries))
        for entry in directory.entries:
            self._data += struct.pack(f"{prefix}HHI", entry.tag, entry.field_type, entry.count)
            self._data += entry.value_field
        self._data += struct.pack(f"{prefix}I", directory.next_offset)
        self._check_size()
        return offset

    def set_ifd0_offset(self, offset: int) -> None:
        """
        Point the header to another IFD0.

        Parameters
        ----------
        offset : int
            The offset of the directory.
        """
        struct.pack_into(
            f"{self._byte_order.struct_prefix}I", self._data, IFD0_OFFSET_POSITION, offset
        )

    def pointer_entry(self, tag: int, offset: int) -> TiffEntry:
        """
        Build the entry of a pointer to a directory.

        Parameters
        ----------
        tag : int
            The pointer tag, such as `ExifOffset` or `GPSInfo`.
        offset : int
            The offset of the directory.

        Returns
        -------
        TiffEntry
            A `LONG` entry holding the offset.
        """
        return self.entry(tag, TiffFieldType.LONG, 1, self._pack("I", offset))

    def bytes_entry(self, tag: int, values: tuple[int, ...]) -> TiffEntry:
        """
        Build the entry of 8-bit unsigned integers, storing them when they do not fit.

        Parameters
        ----------
        tag : int
            The tag id.
        values : tuple[int, ...]
            The integers, each within [0, 255].

        Returns
        -------
        TiffEntry
            A `BYTE` entry.
        """
        return self.entry(tag, TiffFieldType.BYTE, len(values), bytes(values))

    def text_entry(self, tag: int, text: str) -> TiffEntry:
        """
        Build the entry of a text, storing it when it does not fit.

        Parameters
        ----------
        tag : int
            The tag id.
        text : str
            ASCII text, written with its terminating NUL.

        Returns
        -------
        TiffEntry
            An `ASCII` entry.

        Raises
        ------
        UnicodeEncodeError
            If the text is not ASCII.
        """
        encoded = text.encode("ascii") + b"\x00"
        return self.entry(tag, TiffFieldType.ASCII, len(encoded), encoded)

    def rational_entry(self, tag: int, values: tuple[tuple[int, int], ...]) -> TiffEntry:
        """
        Build the entry of unsigned rationals, storing them after the directories.

        Parameters
        ----------
        tag : int
            The tag id.
        values : tuple[tuple[int, int], ...]
            The numerators and denominators, each within 32 bits.

        Returns
        -------
        TiffEntry
            A `RATIONAL` entry.
        """
        data = b"".join(self._pack("II", *value) for value in values)
        return self.entry(tag, TiffFieldType.RATIONAL, len(values), data)

    def entry(self, tag: int, field_type: TiffFieldType, count: int, data: bytes) -> TiffEntry:
        """
        Build an entry, storing its value at the end of the block when it does not fit.

        Parameters
        ----------
        tag : int
            The tag id.
        field_type : TiffFieldType
            The field type.
        count : int
            The number of values.
        data : bytes
            The values, in the byte order of the block.

        Returns
        -------
        TiffEntry
            The entry, holding the value or its offset.
        """
        if len(data) <= VALUE_FIELD_SIZE:
            value_field = data.ljust(VALUE_FIELD_SIZE, b"\x00")
        else:
            offset = self._align()
            self._data += data
            self._check_size()
            value_field = self._pack("I", offset)
        return TiffEntry(tag=tag, field_type=int(field_type), count=count, value_field=value_field)

    def to_bytes(self) -> bytes:
        """
        Return the block as it stands.

        Returns
        -------
        bytes
            The header, the original contents and everything appended.
        """
        return bytes(self._data)

    def _read_entry(self, position: int) -> TiffEntry:
        prefix = self._byte_order.struct_prefix
        tag, field_type, count = struct.unpack_from(f"{prefix}HHI", self._data, position)
        value_start = position + 8
        return TiffEntry(
            tag=tag,
            field_type=field_type,
            count=count,
            value_field=bytes(self._data[value_start : value_start + VALUE_FIELD_SIZE]),
        )

    def _align(self) -> int:
        if len(self._data) % WORD_SIZE:
            self._data += b"\x00"
        return len(self._data)

    def _check_size(self) -> None:
        if len(self._data) > MAXIMUM_OFFSET:
            raise ValueError("TIFF block exceeds 4 GiB")

    def _pack(self, format_code: str, *values: int) -> bytes:
        return struct.pack(f"{self._byte_order.struct_prefix}{format_code}", *values)

    def _unpack(self, format_code: str, offset: int) -> int:
        if offset < 0 or offset + struct.calcsize(format_code) > len(self._data):
            raise ValueError(f"Offset {offset} lies outside the TIFF block")
        value: int = struct.unpack_from(
            f"{self._byte_order.struct_prefix}{format_code}", self._data, offset
        )[0]
        return value

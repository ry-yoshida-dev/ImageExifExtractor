from __future__ import annotations

import uuid
from os import PathLike
from pathlib import Path
from typing import Final

from .exif_update import ExifUpdate
from .exif_update_applier import ExifUpdateApplier
from .jpeg_file import JpegFile
from .tiff_block import TiffBlock

WRITING_SUFFIX: Final[str] = ".writing"


class ExifWriter:
    """
    Write fields of the Exif block of JPEG files without re-encoding the image.

    Only the Exif segment is replaced, and in it only the directories that change are
    written anew, so the compressed pixels, the other segments, the thumbnail and the
    maker note are kept byte for byte. A file without Exif gets a new block. Each
    edit leaves the replaced directories unused in the block, a few hundred bytes.

    XMP metadata, which some applications write besides Exif, is not changed.

    Parameters
    ----------
    applier : ExifUpdateApplier | None
        Sets the fields in the TIFF block; the default one when None.
    """

    def __init__(self, applier: ExifUpdateApplier | None = None) -> None:
        self._applier: ExifUpdateApplier = applier or ExifUpdateApplier()

    def write(
        self,
        source: str | PathLike[str],
        update: ExifUpdate,
        destination: str | PathLike[str] | None = None,
    ) -> Path:
        """
        Write a JPEG file with updated Exif fields.

        The file is written beside its destination first and then moved in place,
        so an interrupted write never leaves a broken file.

        Parameters
        ----------
        source : str | PathLike[str]
            The JPEG file to read.
        update : ExifUpdate
            The fields to set.
        destination : str | PathLike[str] | None
            Where to write the result, or None to overwrite `source`.

        Returns
        -------
        Path
            The file written.

        Raises
        ------
        FileNotFoundError
            If `source` is not an existing file.
        ValueError
            If `source` is not a JPEG file, holds a malformed Exif block, or the
            updated block does not fit in one segment of 64 KB.
        """
        source_path = Path(source)
        if not source_path.is_file():
            raise FileNotFoundError(f"File not found: {source_path}")
        target = source_path if destination is None else Path(destination)
        updated = self.update_bytes(source_path.read_bytes(), update)
        working = target.with_name(f".{target.name}.{uuid.uuid4().hex}{WRITING_SUFFIX}")
        try:
            working.write_bytes(updated)
            working.replace(target)
        finally:
            working.unlink(missing_ok=True)
        return target

    def update_bytes(self, data: bytes, update: ExifUpdate) -> bytes:
        """
        Return the bytes of a JPEG file with updated Exif fields.

        Parameters
        ----------
        data : bytes
            The JPEG file.
        update : ExifUpdate
            The fields to set.

        Returns
        -------
        bytes
            The updated file.

        Raises
        ------
        ValueError
            If `data` is not a JPEG file, holds a malformed Exif block, or the
            updated block does not fit in one segment of 64 KB.
        """
        jpeg = JpegFile.parse(data)
        tiff = jpeg.exif_tiff
        block = TiffBlock.empty() if tiff is None else TiffBlock(tiff)
        self._applier.apply(block, update)
        return jpeg.with_exif_tiff(block.to_bytes()).to_bytes()

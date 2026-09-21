from collections.abc import Collection, Iterable, Iterator, Mapping
from os import PathLike
from pathlib import Path

from PIL import ExifTags, Image

from .exif import ExifMetadata
from .exif.tags import ExifEntry, ExifIFD, ExifValueNormalizer
from .heif_support import HeifSupport


class ExifExtractor:
    """
    Extract Exif metadata from image files.

    Only the file header is read, so extraction does not decode pixel data.
    HEIF / HEIC images are supported when the `heif` extra is installed.

    Attributes
    ----------
    ifds : tuple[ExifIFD, ...]
        The directories extracted, in `ExifIFD` order.
    is_maker_note_included : bool
        Whether the vendor-specific `MakerNote` blob is kept.
    """

    def __init__(
        self,
        ifds: Collection[ExifIFD] = tuple(ExifIFD),
        is_maker_note_included: bool = False,
    ) -> None:
        """
        Initialize the ExifExtractor.

        Parameters
        ----------
        ifds : Collection[ExifIFD]
            The directories to extract. Defaults to every directory.
        is_maker_note_included : bool
            Whether to keep the `MakerNote` tag, an opaque vendor-specific
            blob that is often several kilobytes long.

        Raises
        ------
        ValueError
            If `ifds` is empty.
        """
        if len(ifds) == 0:
            raise ValueError("ifds must contain at least one ExifIFD")

        if HeifSupport.is_available():
            HeifSupport.register()

        self.ifds: tuple[ExifIFD, ...] = tuple(ifd for ifd in ExifIFD if ifd in ifds)
        self.is_maker_note_included: bool = is_maker_note_included

    def extract(self, path: str | PathLike[str]) -> ExifMetadata:
        """
        Extract the Exif metadata of one image file.

        Parameters
        ----------
        path : str | PathLike[str]
            The image file to read.

        Returns
        -------
        ExifMetadata
            The extracted metadata, empty when the image carries no Exif.

        Raises
        ------
        FileNotFoundError
            If `path` is not an existing file.
        PIL.UnidentifiedImageError
            If the file is not an image format Pillow can open.
        TypeError
            If a tag holds a value of a type Exif does not define.
        """
        image_path = Path(path)
        if not image_path.is_file():
            raise FileNotFoundError(f"File not found: {image_path}")

        with Image.open(image_path) as image:
            exif = image.getexif()
            entries = tuple(entry for ifd in self.ifds for entry in self._read_entries(exif, ifd))

        return ExifMetadata(path=image_path, entries=entries)

    def extract_all(self, paths: Iterable[str | PathLike[str]]) -> Iterator[ExifMetadata]:
        """
        Extract the Exif metadata of several image files lazily.

        Parameters
        ----------
        paths : Iterable[str | PathLike[str]]
            The image files to read.

        Returns
        -------
        Iterator[ExifMetadata]
            The metadata of each file, in the order of `paths`.

        Raises
        ------
        FileNotFoundError
            If a path is not an existing file, raised when it is reached.
        PIL.UnidentifiedImageError
            If a file is not an image format Pillow can open.
        """
        for path in paths:
            yield self.extract(path)

    def _read_entries(self, exif: Image.Exif, ifd: ExifIFD) -> Iterator[ExifEntry]:
        """
        Read the entries of one directory, skipping pointers to nested directories.

        Parameters
        ----------
        exif : Image.Exif
            The Exif block of an open image.
        ifd : ExifIFD
            The directory to read.

        Returns
        -------
        Iterator[ExifEntry]
            The entries of `ifd`, in directory order.
        """
        excluded_tag_ids = ExifIFD.pointer_tag_ids()
        if not self.is_maker_note_included:
            excluded_tag_ids |= {int(ExifTags.Base.MakerNote)}

        for tag_id, raw_value in self._read_raw_ifd(exif, ifd).items():
            if tag_id in excluded_tag_ids:
                continue
            yield ExifEntry(
                ifd=ifd,
                tag_id=tag_id,
                value=ExifValueNormalizer.normalize(raw_value),
            )

    @staticmethod
    def _read_raw_ifd(exif: Image.Exif, ifd: ExifIFD) -> Mapping[int, object]:
        """
        Read the raw Pillow values of one directory.

        Parameters
        ----------
        exif : Image.Exif
            The Exif block of an open image.
        ifd : ExifIFD
            The directory to read.

        Returns
        -------
        Mapping[int, object]
            Raw values keyed by tag id, empty when the directory is absent.
        """
        match ifd:
            case ExifIFD.BASE:
                return dict(exif)
            case ExifIFD.EXIF:
                return exif.get_ifd(ExifTags.IFD.Exif)
            case ExifIFD.GPS:
                return exif.get_ifd(ExifTags.IFD.GPSInfo)
            case ExifIFD.INTEROPERABILITY:
                if ExifTags.IFD.Interop not in exif.get_ifd(ExifTags.IFD.Exif):
                    return {}
                return exif.get_ifd(ExifTags.IFD.Interop)

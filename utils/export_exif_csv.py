"""
Export the Exif tags of every image in a directory to one CSV file.

Examples
--------
python utils/export_exif_csv.py image --output exif.csv
python utils/export_exif_csv.py image --tag Make --tag FNumber --tag DateTimeOriginal --gps
python utils/export_exif_csv.py image --recursive
"""

import csv
import json
import sys
from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Sequence
from pathlib import Path
from typing import ClassVar, TextIO

from PIL import Image

from image_exif_extractor import ExifExtractor, ExifIFD, ExifMetadata, ExifValue
from image_exif_extractor.exif.tags import ExifJsonConverter


class ExifCsvExporter:
    """
    Write one CSV row per image file, holding the selected Exif tags.

    Columns are the file path relative to the scanned directory, one column
    per selected tag, optionally the decimal GPS location, and an error
    message for a file that could not be read. Such a file keeps its row with
    empty tag cells, so one broken image does not stop the export.

    Text is written as-is, numbers as numbers, sequences as a JSON array, and
    an absent tag as an empty cell. GPS columns hold signed decimal degrees
    and meters. The file is UTF-8 with BOM so spreadsheet applications detect
    the encoding.

    Attributes
    ----------
    tag_names : tuple[str, ...]
        The registered names of the exported tags, in column order.
    is_gps_included : bool
        Whether latitude, longitude and altitude columns are added.
    is_recursive : bool
        Whether images in sub-directories are exported too.
    extractor : ExifExtractor
        The extractor reading each image.
    """

    DEFAULT_TAG_NAMES: ClassVar[tuple[str, ...]] = (
        "Make",
        "Model",
        "LensModel",
        "DateTimeOriginal",
        "ExposureTime",
        "FNumber",
        "ISOSpeedRatings",
        "FocalLength",
        "Orientation",
    )
    FILE_HEADER: ClassVar[str] = "file"
    GPS_HEADERS: ClassVar[tuple[str, ...]] = ("latitude", "longitude", "altitude")
    ERROR_HEADER: ClassVar[str] = "error"
    OUTPUT_ENCODING: ClassVar[str] = "utf-8-sig"

    def __init__(
        self,
        tag_names: Sequence[str] = DEFAULT_TAG_NAMES,
        is_gps_included: bool = False,
        is_recursive: bool = False,
    ) -> None:
        """
        Initialize the ExifCsvExporter.

        Parameters
        ----------
        tag_names : Sequence[str]
            Names of the tags to export, e.g. `FNumber` or `GPSLatitude`,
            matched case-insensitively. The directory a tag is stored in does
            not need to be given.
        is_gps_included : bool
            Whether to add latitude and longitude in signed decimal degrees,
            and altitude in meters.
        is_recursive : bool
            Whether to include images in sub-directories.

        Raises
        ------
        ValueError
            If a tag name is not a registered Exif tag, or no column would be
            exported.
        """
        if len(tag_names) == 0 and not is_gps_included:
            raise ValueError("Select at least one tag, or include the GPS location")

        registered_names = self._registered_tag_names()
        unknown_names = [name for name in tag_names if name.casefold() not in registered_names]
        if unknown_names:
            raise ValueError(f"Unknown Exif tags: {', '.join(unknown_names)}")

        self.tag_names: tuple[str, ...] = tuple(
            registered_names[name.casefold()] for name in tag_names
        )
        self.is_gps_included: bool = is_gps_included
        self.is_recursive: bool = is_recursive
        self.extractor: ExifExtractor = ExifExtractor()

    @property
    def headers(self) -> list[str]:
        """
        Header row of the CSV file.

        Returns
        -------
        list[str]
            The column names, in column order.
        """
        gps_headers = list(self.GPS_HEADERS) if self.is_gps_included else []
        return [self.FILE_HEADER, *self.tag_names, *gps_headers, self.ERROR_HEADER]

    def image_paths_in(self, directory: Path) -> list[Path]:
        """
        List the image files of a directory that Pillow can open.

        Parameters
        ----------
        directory : Path
            The directory to scan.

        Returns
        -------
        list[Path]
            The image files, sorted by path.

        Raises
        ------
        NotADirectoryError
            If `directory` is not an existing directory.
        """
        if not directory.is_dir():
            raise NotADirectoryError(f"Directory not found: {directory}")

        extensions = {
            extension
            for extension, image_format in Image.registered_extensions().items()
            if image_format in Image.OPEN
        }
        candidates = directory.rglob("*") if self.is_recursive else directory.glob("*")
        return sorted(
            path for path in candidates if path.is_file() and path.suffix.lower() in extensions
        )

    def export(self, directory: Path, output: TextIO) -> int:
        """
        Write the CSV rows of every image in a directory.

        Parameters
        ----------
        directory : Path
            The directory to scan.
        output : TextIO
            The stream to write, opened with `newline=""`.

        Returns
        -------
        int
            The number of files that could not be read.

        Raises
        ------
        NotADirectoryError
            If `directory` is not an existing directory.
        """
        image_paths = self.image_paths_in(directory)
        empty_cells = [""] * (len(self.headers) - 2)

        writer = csv.writer(output)
        writer.writerow(self.headers)
        failed_count = 0
        for path in image_paths:
            try:
                cells = self._build_cells(self.extractor.extract(path))
                error_message = ""
            except (OSError, TypeError, ValueError) as error:
                cells = empty_cells
                error_message = f"{type(error).__name__}: {error}"
                failed_count += 1
            writer.writerow([path.relative_to(directory).as_posix(), *cells, error_message])
        return failed_count

    @classmethod
    def run_command_line(cls, arguments: Sequence[str]) -> int:
        """
        Parse the command line arguments and export the CSV file.

        Parameters
        ----------
        arguments : Sequence[str]
            The command line arguments, without the program name.

        Returns
        -------
        int
            The process exit status: 0 when every image was read, 1 otherwise.
        """
        parser = ArgumentParser(
            description="Export the Exif tags of every image in a directory to a CSV file.",
        )
        parser.add_argument(
            "directory",
            nargs="?",
            type=cls._existing_directory,
            default="image",
            help="directory holding the images (default: image)",
        )
        parser.add_argument(
            "-o",
            "--output",
            type=Path,
            default=Path("exif.csv"),
            help="CSV file to write (default: exif.csv)",
        )
        parser.add_argument(
            "-t",
            "--tag",
            dest="tag_names",
            action="append",
            metavar="TAG",
            help="Exif tag name to export, repeatable (default: "
            + ", ".join(cls.DEFAULT_TAG_NAMES)
            + ")",
        )
        parser.add_argument(
            "--gps",
            dest="is_gps_included",
            action="store_true",
            help="add latitude, longitude and altitude columns",
        )
        parser.add_argument(
            "-r",
            "--recursive",
            dest="is_recursive",
            action="store_true",
            help="include images in sub-directories",
        )
        namespace = parser.parse_args(arguments)
        directory: Path = namespace.directory
        output_path: Path = namespace.output
        tag_names: list[str] = namespace.tag_names or list(cls.DEFAULT_TAG_NAMES)
        is_gps_included: bool = namespace.is_gps_included
        is_recursive: bool = namespace.is_recursive

        try:
            exporter = cls(
                tag_names=tag_names,
                is_gps_included=is_gps_included,
                is_recursive=is_recursive,
            )
        except ValueError as error:
            parser.error(str(error))

        with output_path.open("w", newline="", encoding=cls.OUTPUT_ENCODING) as output:
            failed_count = exporter.export(directory, output)

        print(f"Wrote {output_path}, unreadable files: {failed_count}", file=sys.stderr)
        return 1 if failed_count > 0 else 0

    def _build_cells(self, metadata: ExifMetadata) -> list[str]:
        """
        Build the tag and GPS cells of one image.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata of the image.

        Returns
        -------
        list[str]
            The cells between the file and error columns.

        Raises
        ------
        ValueError
            If the GPS tags are malformed.
        TypeError
            If a GPS tag holds a value of an unexpected type.
        """
        values = [self._find_value_by_name(metadata, name) for name in self.tag_names]
        tag_cells = ["" if value is None else self._format(value) for value in values]
        if not self.is_gps_included:
            return tag_cells
        return [*tag_cells, *self._build_gps_cells(metadata)]

    @staticmethod
    def _build_gps_cells(metadata: ExifMetadata) -> list[str]:
        """
        Build the latitude, longitude and altitude cells of one image.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata of the image.

        Returns
        -------
        list[str]
            Signed decimal degrees and meters, empty when unrecorded.
        """
        coordinate = metadata.gps_coordinate
        if coordinate is None:
            return ["", "", ""]
        altitude = coordinate.altitude
        return [
            str(float(coordinate.latitude.degree[0])),
            str(float(coordinate.longitude.degree[0])),
            "" if altitude is None else str(float(altitude.meter[0])),
        ]

    @staticmethod
    def _find_value_by_name(metadata: ExifMetadata, tag_name: str) -> ExifValue | None:
        """
        Find the value of a tag in whichever directory stores it.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata of the image.
        tag_name : str
            The registered tag name.

        Returns
        -------
        ExifValue | None
            The value, or None when the image does not carry the tag.
        """
        return next((entry.value for entry in metadata.entries if entry.name == tag_name), None)

    @staticmethod
    def _format(value: ExifValue) -> str:
        """
        Format a tag value as one CSV cell.

        Parameters
        ----------
        value : ExifValue
            The value.

        Returns
        -------
        str
            Text as-is, numbers in Python notation, sequences as a JSON
            array, and an empty cell for undefined values.
        """
        match ExifJsonConverter.convert(value):
            case None:
                return ""
            case str() as text:
                return text
            case converted:
                return json.dumps(converted, ensure_ascii=False)

    @staticmethod
    def _registered_tag_names() -> dict[str, str]:
        """
        Collect the registered name of every Exif tag.

        Returns
        -------
        dict[str, str]
            Registered names keyed by their case-folded form.
        """
        return {name.casefold(): name for ifd in ExifIFD for name in ifd.tag_names.values()}

    @staticmethod
    def _existing_directory(text: str) -> Path:
        """
        Convert an argument into the path of an existing directory.

        Parameters
        ----------
        text : str
            The argument as typed.

        Returns
        -------
        Path
            The path.

        Raises
        ------
        ArgumentTypeError
            If the path is not an existing directory.
        """
        path = Path(text)
        if not path.is_dir():
            raise ArgumentTypeError(f"directory not found: {text}")
        return path


if __name__ == "__main__":
    sys.exit(ExifCsvExporter.run_command_line(sys.argv[1:]))

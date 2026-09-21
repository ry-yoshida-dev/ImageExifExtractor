"""
Print the Exif metadata of images as a JSON array.

Examples
--------
python utils/print_exif_json.py photo1.jpg photo2.jpg
python utils/print_exif_json.py photo.jpg --ifd base --ifd gps --indent 0
python utils/print_exif_json.py photo.jpg --include-maker-note
"""

import json
import sys
from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Sequence
from pathlib import Path

from image_exif_extractor import ExifExtractor, ExifIFD, JsonValue


class ExifJsonPrinter:
    """
    Command line interface printing the Exif metadata of images as JSON.

    Attributes
    ----------
    parser : ArgumentParser
        The parser for the command line arguments.
    """

    def __init__(self) -> None:
        self.parser: ArgumentParser = self._build_parser()

    def run(self, arguments: Sequence[str]) -> int:
        """
        Extract the metadata of the given images and print it to stdout.

        A file that cannot be read is reported to stderr and skipped, so the
        remaining files are still printed.

        Parameters
        ----------
        arguments : Sequence[str]
            The command line arguments, without the program name.

        Returns
        -------
        int
            The process exit status: 0 when every file was read, 1 otherwise.
        """
        namespace = self.parser.parse_args(arguments)
        paths: list[Path] = namespace.paths
        ifds: list[ExifIFD] = namespace.ifds or list(ExifIFD)
        is_maker_note_included: bool = namespace.is_maker_note_included
        indent: int = namespace.indent

        extractor = ExifExtractor(ifds=ifds, is_maker_note_included=is_maker_note_included)
        documents: list[JsonValue] = []
        failed_paths: list[Path] = []
        for path in paths:
            try:
                documents.append(extractor.extract(path).to_json_dict())
            except (OSError, TypeError, ValueError) as error:
                failed_paths.append(path)
                print(f"{path}: {type(error).__name__}: {error}", file=sys.stderr)

        print(json.dumps(documents, indent=indent, ensure_ascii=False))
        return 1 if failed_paths else 0

    @staticmethod
    def _build_parser() -> ArgumentParser:
        """
        Build the parser for the command line arguments.

        Returns
        -------
        ArgumentParser
            The configured parser.
        """
        parser = ArgumentParser(
            description="Print the Exif metadata of images as a JSON array.",
        )
        parser.add_argument(
            "paths",
            nargs="+",
            type=ExifJsonPrinter._existing_file,
            help="image files to read",
        )
        parser.add_argument(
            "--ifd",
            dest="ifds",
            action="append",
            type=ExifIFD,
            choices=list(ExifIFD),
            metavar="{" + ",".join(ifd.value for ifd in ExifIFD) + "}",
            help="directory to extract, repeatable (default: all)",
        )
        parser.add_argument(
            "--include-maker-note",
            dest="is_maker_note_included",
            action="store_true",
            help="keep the vendor-specific MakerNote blob",
        )
        parser.add_argument(
            "--indent",
            type=ExifJsonPrinter._non_negative_integer,
            default=2,
            help="JSON indentation width (default: 2)",
        )
        return parser

    @staticmethod
    def _existing_file(text: str) -> Path:
        """
        Convert an argument into the path of an existing file.

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
            If the path is not an existing file.
        """
        path = Path(text)
        if not path.is_file():
            raise ArgumentTypeError(f"file not found: {text}")
        return path

    @staticmethod
    def _non_negative_integer(text: str) -> int:
        """
        Convert an argument into a non-negative integer.

        Parameters
        ----------
        text : str
            The argument as typed.

        Returns
        -------
        int
            The integer.

        Raises
        ------
        ArgumentTypeError
            If the argument is not an integer of zero or more.
        """
        if not text.isdigit():
            raise ArgumentTypeError(f"expected a non-negative integer, given: {text}")
        return int(text)


if __name__ == "__main__":
    sys.exit(ExifJsonPrinter().run(sys.argv[1:]))

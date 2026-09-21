from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from PIL.ExifTags import Base

from ..tags import ExifIFD
from .datetime_parser import ExifDateTimeParser

if TYPE_CHECKING:
    from ..metadata import ExifMetadata


@dataclass(frozen=True)
class CaptureSettings:
    """
    Exposure settings and time of capture of an image.

    Attributes
    ----------
    exposure_time : float | None
        Exposure time in seconds.
    f_number : float | None
        Aperture as an f-number.
    iso : int | None
        ISO sensitivity.
    focal_length : float | None
        Actual focal length of the lens in millimeters.
    focal_length_in_35mm_film : int | None
        Focal length equivalent on 35 mm film in millimeters.
    captured_at : datetime | None
        When the image was captured, timezone-aware when the offset is known.
    """

    exposure_time: float | None
    f_number: float | None
    iso: int | None
    focal_length: float | None
    focal_length_in_35mm_film: int | None
    captured_at: datetime | None

    @classmethod
    def from_metadata(cls, metadata: ExifMetadata) -> CaptureSettings:
        """
        Read the capture settings from extracted metadata.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata to read.

        Returns
        -------
        CaptureSettings
            The capture settings, with None for each absent field.

        Raises
        ------
        TypeError
            If one of the tags holds a value of an unexpected type.
        ValueError
            If the date-time tags do not follow the Exif format.
        """
        focal_length_in_35mm_film = metadata.find_number(ExifIFD.EXIF, Base.FocalLengthIn35mmFilm)
        return cls(
            exposure_time=metadata.find_number(ExifIFD.EXIF, Base.ExposureTime),
            f_number=metadata.find_number(ExifIFD.EXIF, Base.FNumber),
            iso=cls._read_iso(metadata),
            focal_length=metadata.find_number(ExifIFD.EXIF, Base.FocalLength),
            focal_length_in_35mm_film=(
                None if focal_length_in_35mm_film is None else int(focal_length_in_35mm_film)
            ),
            captured_at=cls._read_captured_at(metadata),
        )

    @staticmethod
    def _read_iso(metadata: ExifMetadata) -> int | None:
        """
        Read the ISO sensitivity, which some cameras store as a sequence.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata to read.

        Returns
        -------
        int | None
            The first ISO value, or None when the tag is absent.

        Raises
        ------
        TypeError
            If the tag holds neither an integer nor a sequence of integers.
        """
        match metadata.find_value(ExifIFD.EXIF, Base.ISOSpeedRatings):
            case None:
                return None
            case int() as iso:
                return iso
            case (int() as iso, *_):
                return iso
            case value:
                raise TypeError(f"Tag ISOSpeedRatings holds {type(value).__name__}, expected int")

    @staticmethod
    def _read_captured_at(metadata: ExifMetadata) -> datetime | None:
        """
        Read the capture time, falling back to the file modification time tag.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata to read.

        Returns
        -------
        datetime | None
            `DateTimeOriginal` when present and known, otherwise `DateTime`,
            or None when neither is present and known.
        """
        original_text = metadata.find_text(ExifIFD.EXIF, Base.DateTimeOriginal)
        if original_text is not None:
            original = ExifDateTimeParser.parse(
                date_time_text=original_text,
                offset_text=metadata.find_text(ExifIFD.EXIF, Base.OffsetTimeOriginal),
                subsecond_text=metadata.find_text(ExifIFD.EXIF, Base.SubsecTimeOriginal),
            )
            if original is not None:
                return original

        modified_text = metadata.find_text(ExifIFD.BASE, Base.DateTime)
        if modified_text is None:
            return None
        return ExifDateTimeParser.parse(
            date_time_text=modified_text,
            offset_text=metadata.find_text(ExifIFD.EXIF, Base.OffsetTime),
            subsecond_text=metadata.find_text(ExifIFD.EXIF, Base.SubsecTime),
        )

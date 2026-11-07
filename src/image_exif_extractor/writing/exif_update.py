from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from geo_coordinate import Bearing, GeoCoordinate


@dataclass(frozen=True)
class ExifUpdate:
    """
    The fields to set in the Exif block of an image; fields left None are kept.

    Latitudes and longitudes are written to a ten-thousandth of an arcsecond, about
    3 mm, and directions and altitudes to a hundredth.

    Attributes
    ----------
    location : GeoCoordinate | None
        Where the image was captured. Its altitude replaces the recorded one, and a
        location without altitude removes the recorded altitude, which belonged to
        the former location.
    image_direction : Bearing | None
        The direction the camera faced, from true or magnetic north.
    captured_at : datetime | None
        When the image was captured, written as `DateTimeOriginal`, with
        `OffsetTimeOriginal` when it is timezone-aware. The recorded subseconds are
        removed, since they belonged to the former time.

    Raises
    ------
    ValueError
        If no field is set, or `image_direction` holds more than one bearing.
    """

    location: GeoCoordinate | None = None
    image_direction: Bearing | None = None
    captured_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.location is None and self.image_direction is None and self.captured_at is None:
            raise ValueError("An Exif update must set at least one field")
        if self.image_direction is not None and len(self.image_direction) != 1:
            raise ValueError(
                f"image_direction must hold one bearing, given: {len(self.image_direction)}"
            )

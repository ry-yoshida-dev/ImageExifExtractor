from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
from geo_coordinate import Altitude, GeoCoordinate, LatitudeHemisphere, LongitudeHemisphere
from PIL.ExifTags import GPS
from units import Angle, DegreesMinutesSeconds, Length, LengthUnit

from ..tags import ExifIFD, ExifValue
from .altitude_reference import AltitudeReference

if TYPE_CHECKING:
    from ..metadata import ExifMetadata


class GpsCoordinateReader:
    """
    Read the GPS directory of extracted metadata into a `GeoCoordinate`.

    Exif stores each angle as an unsigned degrees-minutes-seconds triple with
    a separate hemisphere reference, and the altitude as an unsigned height
    with a separate sea level reference. Both are combined into signed values.
    """

    @classmethod
    def from_metadata(cls, metadata: ExifMetadata) -> GeoCoordinate | None:
        """
        Read the location an image was captured at.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata to read.

        Returns
        -------
        GeoCoordinate | None
            A single coordinate, or None when latitude or longitude is absent
            or undefined (a rational with a zero denominator).

        Raises
        ------
        ValueError
            If a coordinate is present without its hemisphere reference, or a
            tag holds a malformed value.
        TypeError
            If a tag holds a value of an unexpected type.
        """
        latitude_value = metadata.find_value(ExifIFD.GPS, GPS.GPSLatitude)
        longitude_value = metadata.find_value(ExifIFD.GPS, GPS.GPSLongitude)
        if latitude_value is None or longitude_value is None:
            return None
        if cls._is_undefined(latitude_value) or cls._is_undefined(longitude_value):
            return None

        latitude_reference_text = metadata.find_text(ExifIFD.GPS, GPS.GPSLatitudeRef)
        if latitude_reference_text is None:
            raise ValueError("GPSLatitude is present without GPSLatitudeRef")
        longitude_reference_text = metadata.find_text(ExifIFD.GPS, GPS.GPSLongitudeRef)
        if longitude_reference_text is None:
            raise ValueError("GPSLongitude is present without GPSLongitudeRef")

        latitude = cls._to_sexagesimal(
            latitude_value, LatitudeHemisphere(latitude_reference_text).is_negative
        )
        longitude = cls._to_sexagesimal(
            longitude_value, LongitudeHemisphere(longitude_reference_text).is_negative
        )
        return GeoCoordinate(
            latitude=Angle.from_degrees_minutes_seconds(latitude),
            longitude=Angle.from_degrees_minutes_seconds(longitude),
            altitude=cls._read_altitude(metadata),
        )

    @staticmethod
    def _is_undefined(value: ExifValue) -> bool:
        """
        Whether an angle holds a rational with a zero denominator.

        Parameters
        ----------
        value : ExifValue
            `(degrees, minutes, seconds)`, or plain decimal degrees.

        Returns
        -------
        bool
            True when any component normalized to NaN.
        """
        match value:
            case float():
                return math.isnan(value)
            case tuple():
                return any(GpsCoordinateReader._is_undefined(component) for component in value)
            case _:
                return False

    @staticmethod
    def _to_sexagesimal(value: ExifValue, is_negative: bool) -> DegreesMinutesSeconds:
        """
        Convert an unsigned Exif angle and its hemisphere into a signed sexagesimal angle.

        Writers do not always store canonical components, e.g. fractional
        minutes with zero seconds, so the components are carried into
        canonical form.

        Parameters
        ----------
        value : ExifValue
            `(degrees, minutes, seconds)`, or plain decimal degrees.
        is_negative : bool
            Whether the hemisphere is southern or western.

        Returns
        -------
        DegreesMinutesSeconds
            A single signed angle.

        Raises
        ------
        ValueError
            If the value is neither a number nor a triple of non-negative numbers.
        """
        match value:
            case (
                int() | float() as degrees,
                int() | float() as minutes,
                int() | float() as seconds,
            ):
                return DegreesMinutesSeconds.normalized(
                    degrees=np.array([degrees], dtype=np.float64),
                    minutes=np.array([minutes], dtype=np.float64),
                    seconds=np.array([seconds], dtype=np.float64),
                    is_negative=np.array([is_negative]),
                )
            case int() | float():
                return GpsCoordinateReader._to_sexagesimal((value, 0, 0), is_negative)
            case _:
                raise ValueError(f"Expected (degrees, minutes, seconds), given: {value!r}")

    @staticmethod
    def _read_altitude(metadata: ExifMetadata) -> Altitude | None:
        """
        Read the signed altitude.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata to read.

        Returns
        -------
        Altitude | None
            A single altitude in meters, or None when it is absent or undefined.
            An absent sea level reference means above sea level, as the Exif
            specification defines.
        """
        height = metadata.find_number(ExifIFD.GPS, GPS.GPSAltitude)
        if height is None:
            return None
        reference_value = metadata.find_value(ExifIFD.GPS, GPS.GPSAltitudeRef)
        reference = (
            AltitudeReference.ABOVE_SEA_LEVEL
            if reference_value is None
            else AltitudeReference.from_value(reference_value)
        )
        return Altitude.from_magnitude(
            magnitude=Length(value=np.array([height]), unit=LengthUnit.M),
            is_below_sea_level=np.array([reference.is_below_sea_level]),
        )

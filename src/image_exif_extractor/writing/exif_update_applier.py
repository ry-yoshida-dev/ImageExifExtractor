from __future__ import annotations

from datetime import datetime
from typing import Final

from geo_coordinate import Altitude, Bearing, GeoCoordinate, LatitudeHemisphere, LongitudeHemisphere
from PIL.ExifTags import GPS, IFD, Base

from .exif_update import ExifUpdate
from .tiff_block import TiffBlock
from .tiff_directory import TiffDirectory

GPS_VERSION: Final[tuple[int, ...]] = (2, 3, 0, 0)
SECONDS_DENOMINATOR: Final[int] = 10_000
SECONDS_PER_DEGREE: Final[int] = 3_600
SECONDS_PER_MINUTE: Final[int] = 60
HUNDREDTHS: Final[int] = 100
MINUTES_PER_HOUR: Final[int] = 60
FIRST_ELEMENT: Final[int] = 0


class ExifUpdateApplier:
    """
    Sets the fields of an `ExifUpdate` in a TIFF block of Exif.

    The GPS and Exif directories that change are written anew at the end of the
    block, keeping their other entries, and IFD0 is written anew pointing to them,
    so the thumbnail directory, the maker note and every other value keep their
    offsets. A missing GPS or Exif directory is created.
    """

    def apply(self, block: TiffBlock, update: ExifUpdate) -> None:
        """
        Set the fields of an update in a block.

        Parameters
        ----------
        block : TiffBlock
            The block to edit.
        update : ExifUpdate
            The fields to set.

        Raises
        ------
        ValueError
            If the block holds a malformed directory.
        """
        ifd0 = block.read_directory(block.ifd0_offset)
        if update.location is not None or update.image_direction is not None:
            gps = self._sub_directory(block, ifd0, IFD.GPSInfo)
            if update.location is not None:
                gps = self._located(block, gps, update.location)
            if update.image_direction is not None:
                gps = self._directed(block, gps, update.image_direction)
            ifd0 = ifd0.with_entry(
                block.pointer_entry(int(IFD.GPSInfo), block.append_directory(gps))
            )
        if update.captured_at is not None:
            exif = self._dated(
                block, self._sub_directory(block, ifd0, IFD.Exif), update.captured_at
            )
            ifd0 = ifd0.with_entry(block.pointer_entry(int(IFD.Exif), block.append_directory(exif)))
        block.set_ifd0_offset(block.append_directory(ifd0))

    @staticmethod
    def _sub_directory(block: TiffBlock, ifd0: TiffDirectory, pointer: IFD) -> TiffDirectory:
        offset = block.pointer_of(ifd0, int(pointer))
        return TiffDirectory(entries=()) if offset is None else block.read_directory(offset)

    def _located(
        self, block: TiffBlock, gps: TiffDirectory, location: GeoCoordinate
    ) -> TiffDirectory:
        latitude = float(location.latitude.degree[FIRST_ELEMENT])
        longitude = float(location.longitude.degree[FIRST_ELEMENT])
        if gps.find(int(GPS.GPSVersionID)) is None:
            gps = gps.with_entry(block.bytes_entry(int(GPS.GPSVersionID), GPS_VERSION))
        gps = (
            gps.with_entry(
                block.text_entry(
                    int(GPS.GPSLatitudeRef), LatitudeHemisphere.from_is_negative(latitude < 0).value
                )
            )
            .with_entry(block.rational_entry(int(GPS.GPSLatitude), self._sexagesimal(latitude)))
            .with_entry(
                block.text_entry(
                    int(GPS.GPSLongitudeRef),
                    LongitudeHemisphere.from_is_negative(longitude < 0).value,
                )
            )
            .with_entry(block.rational_entry(int(GPS.GPSLongitude), self._sexagesimal(longitude)))
        )
        if location.altitude is None:
            return gps.without(int(GPS.GPSAltitudeRef), int(GPS.GPSAltitude))
        return self._with_altitude(block, gps, location.altitude)

    @staticmethod
    def _with_altitude(block: TiffBlock, gps: TiffDirectory, altitude: Altitude) -> TiffDirectory:
        is_below = bool(altitude.is_below_sea_level[FIRST_ELEMENT])
        height = float(altitude.magnitude.meter[FIRST_ELEMENT])
        return gps.with_entry(
            block.bytes_entry(int(GPS.GPSAltitudeRef), (int(is_below),))
        ).with_entry(
            block.rational_entry(int(GPS.GPSAltitude), ((round(height * HUNDREDTHS), HUNDREDTHS),))
        )

    @staticmethod
    def _directed(block: TiffBlock, gps: TiffDirectory, bearing: Bearing) -> TiffDirectory:
        degree = float(bearing.degree[FIRST_ELEMENT])
        hundredths = round(degree * HUNDREDTHS) % (360 * HUNDREDTHS)
        return gps.with_entry(
            block.text_entry(int(GPS.GPSImgDirectionRef), bearing.reference.value)
        ).with_entry(block.rational_entry(int(GPS.GPSImgDirection), ((hundredths, HUNDREDTHS),)))

    @staticmethod
    def _dated(block: TiffBlock, exif: TiffDirectory, captured_at: datetime) -> TiffDirectory:
        date_time = (
            f"{captured_at.year:04d}:{captured_at.month:02d}:{captured_at.day:02d} "
            + f"{captured_at.hour:02d}:{captured_at.minute:02d}:{captured_at.second:02d}"
        )
        exif = exif.with_entry(block.text_entry(int(Base.DateTimeOriginal), date_time)).without(
            int(Base.SubsecTimeOriginal)
        )
        offset = captured_at.utcoffset()
        if offset is None:
            return exif.without(int(Base.OffsetTimeOriginal))
        total_minutes = round(offset.total_seconds() / SECONDS_PER_MINUTE)
        sign = "-" if total_minutes < 0 else "+"
        hours, minutes = divmod(abs(total_minutes), MINUTES_PER_HOUR)
        return exif.with_entry(
            block.text_entry(int(Base.OffsetTimeOriginal), f"{sign}{hours:02d}:{minutes:02d}")
        )

    @staticmethod
    def _sexagesimal(degree: float) -> tuple[tuple[int, int], ...]:
        total = round(abs(degree) * SECONDS_PER_DEGREE * SECONDS_DENOMINATOR)
        degrees, remainder = divmod(total, SECONDS_PER_DEGREE * SECONDS_DENOMINATOR)
        minutes, seconds = divmod(remainder, SECONDS_PER_MINUTE * SECONDS_DENOMINATOR)
        return ((degrees, 1), (minutes, 1), (seconds, SECONDS_DENOMINATOR))

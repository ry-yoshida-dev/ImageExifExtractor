import math
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from geo_coordinate import Bearing, GeoCoordinate

from ..xmp import DroneAttitude, DroneAttitudeReader, XmpPacket
from .gps import GpsBearingKind, GpsBearingReader, GpsCoordinateReader
from .summaries import CameraInfo, CaptureSettings, Orientation
from .tags import ExifEntry, ExifIFD, ExifJsonConverter, ExifValue, JsonValue


@dataclass(frozen=True)
class ExifMetadata:
    """
    Exif metadata extracted from one image file.

    Obtained from `ExifExtractor.extract`; constructing it directly is intended
    for tests and synthetic data.

    Raw tags are kept as `ExifEntry` items, and common fields are interpreted on
    first access, then cached, through `camera`, `capture_settings`,
    `gps_coordinate`, `image_direction` and `orientation`.

    Attributes
    ----------
    path : Path
        The image file the metadata was extracted from.
    entries : tuple[ExifEntry, ...]
        Every extracted tag, in directory order.
    xmp : XmpPacket | None
        The XMP metadata of the image, or None when it carries none.
    """

    path: Path
    entries: tuple[ExifEntry, ...]
    xmp: XmpPacket | None = None

    @cached_property
    def _entry_index(self) -> dict[tuple[ExifIFD, int], ExifEntry]:
        return {(entry.ifd, entry.tag_id): entry for entry in self.entries}

    @property
    def is_empty(self) -> bool:
        """
        Whether the image carries no Exif tag at all.

        Returns
        -------
        bool
            True when no tag was extracted.
        """
        return len(self.entries) == 0

    def entries_in(self, ifd: ExifIFD) -> tuple[ExifEntry, ...]:
        """
        Select the entries stored in one directory.

        Parameters
        ----------
        ifd : ExifIFD
            The directory to select.

        Returns
        -------
        tuple[ExifEntry, ...]
            The entries of `ifd`, in directory order.
        """
        return tuple(entry for entry in self.entries if entry.ifd is ifd)

    def find(self, ifd: ExifIFD, tag_id: int) -> ExifEntry | None:
        """
        Look up one tag.

        Parameters
        ----------
        ifd : ExifIFD
            The directory the tag is stored in.
        tag_id : int
            The tag id, e.g. `PIL.ExifTags.Base.Make`.

        Returns
        -------
        ExifEntry | None
            The entry, or None when the image does not carry the tag.
        """
        return self._entry_index.get((ifd, tag_id))

    def find_value(self, ifd: ExifIFD, tag_id: int) -> ExifValue | None:
        """
        Look up the value of one tag.

        Parameters
        ----------
        ifd : ExifIFD
            The directory the tag is stored in.
        tag_id : int
            The tag id, e.g. `PIL.ExifTags.Base.Make`.

        Returns
        -------
        ExifValue | None
            The value, or None when the image does not carry the tag.
        """
        entry = self.find(ifd, tag_id)
        if entry is None:
            return None
        return entry.value

    def find_text(self, ifd: ExifIFD, tag_id: int) -> str | None:
        """
        Look up the value of one text tag.

        Parameters
        ----------
        ifd : ExifIFD
            The directory the tag is stored in.
        tag_id : int
            The tag id, e.g. `PIL.ExifTags.Base.Make`.

        Returns
        -------
        str | None
            The text, or None when the tag is absent or blank.

        Raises
        ------
        TypeError
            If the tag holds a non-text value.
        """
        match self.find_value(ifd, tag_id):
            case None:
                return None
            case str() as text:
                return text or None
            case value:
                raise TypeError(
                    f"Tag {ifd.resolve_tag_name(tag_id)} holds {type(value).__name__}, expected str"
                )

    def find_number(self, ifd: ExifIFD, tag_id: int) -> float | None:
        """
        Look up the value of one numeric tag.

        Parameters
        ----------
        ifd : ExifIFD
            The directory the tag is stored in.
        tag_id : int
            The tag id, e.g. `PIL.ExifTags.Base.FNumber`.

        Returns
        -------
        float | None
            The number, or None when the tag is absent or undefined (a
            rational with a zero denominator, normalized to NaN).

        Raises
        ------
        TypeError
            If the tag holds a non-numeric value.
        """
        match self.find_value(ifd, tag_id):
            case None:
                return None
            case float() as number if math.isnan(number):
                return None
            case int() | float() as number:
                return float(number)
            case value:
                raise TypeError(
                    f"Tag {ifd.resolve_tag_name(tag_id)} holds {type(value).__name__}, "
                    + "expected int or float"
                )

    @cached_property
    def camera(self) -> CameraInfo:
        """
        Camera and lens that captured the image.

        Returns
        -------
        CameraInfo
            The camera description, with None for each absent field.
        """
        return CameraInfo.from_metadata(self)

    @cached_property
    def capture_settings(self) -> CaptureSettings:
        """
        Exposure settings and time of capture.

        Returns
        -------
        CaptureSettings
            The capture settings, with None for each absent field.
        """
        return CaptureSettings.from_metadata(self)

    @cached_property
    def gps_coordinate(self) -> GeoCoordinate | None:
        """
        Location the image was captured at.

        Returns
        -------
        GeoCoordinate | None
            A single coordinate, or None when the image carries no usable location.
        """
        return GpsCoordinateReader.from_metadata(self)

    @cached_property
    def image_direction(self) -> Bearing | None:
        """
        Direction the camera faced when the image was captured.

        Returns
        -------
        Bearing | None
            A single bearing from true or magnetic north, or None when unrecorded.
        """
        return GpsBearingReader.from_metadata(self, GpsBearingKind.IMAGE_DIRECTION)

    @cached_property
    def drone_attitude(self) -> DroneAttitude | None:
        """
        Attitude of a drone's camera, as DJI records it in XMP.

        Returns
        -------
        DroneAttitude | None
            The height above the take-off point and the gimbal angles, or None when
            the image carries no XMP or no drone attitude.

        Raises
        ------
        ValueError
            If a drone property is present but not a finite number.
        """
        return None if self.xmp is None else DroneAttitudeReader.from_packet(self.xmp)

    def gps_bearing(self, kind: GpsBearingKind) -> Bearing | None:
        """
        Read one of the directions the GPS directory records.

        Parameters
        ----------
        kind : GpsBearingKind
            The direction faced, moved in, or towards the destination.

        Returns
        -------
        Bearing | None
            A single bearing from true or magnetic north, or None when unrecorded.

        Raises
        ------
        ValueError
            If the reference is neither `T` nor `M`.
        """
        return GpsBearingReader.from_metadata(self, kind)

    @cached_property
    def orientation(self) -> Orientation | None:
        """
        Orientation the stored pixels must be transformed by for display.

        Returns
        -------
        Orientation | None
            The orientation, or None when the tag is absent.
        """
        return Orientation.from_metadata(self)

    def to_json_dict(self) -> dict[str, JsonValue]:
        """
        Build a JSON-serializable representation, grouped by directory.

        Returns
        -------
        dict[str, JsonValue]
            `path` and one object per directory under `ifds`, mapping tag
            names to their values.
        """
        ifds: dict[str, JsonValue] = {}
        for ifd in ExifIFD:
            tags: dict[str, JsonValue] = {
                entry.name: ExifJsonConverter.convert(entry.value) for entry in self.entries_in(ifd)
            }
            if tags:
                ifds[ifd.value] = tags
        return {"path": str(self.path), "ifds": ifds}

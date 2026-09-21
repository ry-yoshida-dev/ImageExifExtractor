from __future__ import annotations

from enum import IntEnum
from typing import TYPE_CHECKING

from PIL.ExifTags import Base

from ..tags import ExifIFD

if TYPE_CHECKING:
    from ..metadata import ExifMetadata


class Orientation(IntEnum):
    """
    Exif `Orientation` tag, describing how stored pixels map to the displayed image.

    Each member names the transformation that turns the stored pixels into
    the upright image, with rotations measured clockwise.

    Attributes
    ----------
    NORMAL
        Stored upright.
    MIRROR_HORIZONTAL
        Mirror left to right.
    ROTATE_180
        Rotate by 180 degrees.
    MIRROR_VERTICAL
        Mirror top to bottom.
    MIRROR_HORIZONTAL_ROTATE_270
        Mirror left to right, then rotate by 270 degrees.
    ROTATE_90
        Rotate by 90 degrees.
    MIRROR_HORIZONTAL_ROTATE_90
        Mirror left to right, then rotate by 90 degrees.
    ROTATE_270
        Rotate by 270 degrees.
    """

    NORMAL = 1
    MIRROR_HORIZONTAL = 2
    ROTATE_180 = 3
    MIRROR_VERTICAL = 4
    MIRROR_HORIZONTAL_ROTATE_270 = 5
    ROTATE_90 = 6
    MIRROR_HORIZONTAL_ROTATE_90 = 7
    ROTATE_270 = 8

    @property
    def clockwise_rotation_degrees(self) -> int:
        """
        Clockwise rotation applied after any mirroring.

        `MIRROR_VERTICAL` is expressed as a horizontal mirror followed by a
        180 degree rotation.

        Returns
        -------
        int
            One of 0, 90, 180 or 270.
        """
        match self:
            case Orientation.NORMAL | Orientation.MIRROR_HORIZONTAL:
                return 0
            case Orientation.ROTATE_90 | Orientation.MIRROR_HORIZONTAL_ROTATE_90:
                return 90
            case Orientation.ROTATE_180 | Orientation.MIRROR_VERTICAL:
                return 180
            case Orientation.ROTATE_270 | Orientation.MIRROR_HORIZONTAL_ROTATE_270:
                return 270

    @property
    def is_mirrored(self) -> bool:
        """
        Whether a left-to-right mirror precedes the rotation.

        Returns
        -------
        bool
            True for the mirrored orientations.
        """
        match self:
            case (
                Orientation.MIRROR_HORIZONTAL
                | Orientation.MIRROR_VERTICAL
                | Orientation.MIRROR_HORIZONTAL_ROTATE_270
                | Orientation.MIRROR_HORIZONTAL_ROTATE_90
            ):
                return True
            case (
                Orientation.NORMAL
                | Orientation.ROTATE_90
                | Orientation.ROTATE_180
                | Orientation.ROTATE_270
            ):
                return False

    @property
    def is_dimension_swapped(self) -> bool:
        """
        Whether the displayed width and height are swapped from the stored ones.

        Returns
        -------
        bool
            True when the rotation is 90 or 270 degrees.
        """
        return self.clockwise_rotation_degrees in (90, 270)

    @classmethod
    def from_metadata(cls, metadata: ExifMetadata) -> Orientation | None:
        """
        Read the orientation from extracted metadata.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata to read.

        Returns
        -------
        Orientation | None
            The orientation, or None when the tag is absent.

        Raises
        ------
        TypeError
            If the tag holds a non-integer value.
        ValueError
            If the tag holds an integer outside 1 to 8.
        """
        match metadata.find_value(ExifIFD.BASE, Base.Orientation):
            case None:
                return None
            case int() as value:
                return cls(value)
            case value:
                raise TypeError(f"Tag Orientation holds {type(value).__name__}, expected int")

from __future__ import annotations

from enum import IntEnum

from ..tags import ExifValue


class AltitudeReference(IntEnum):
    """
    Exif `GPSAltitudeRef` tag, the side of sea level an altitude is measured on.

    Attributes
    ----------
    ABOVE_SEA_LEVEL
        Altitude above sea level.
    BELOW_SEA_LEVEL
        Altitude below sea level.
    """

    ABOVE_SEA_LEVEL = 0
    BELOW_SEA_LEVEL = 1

    @property
    def is_below_sea_level(self) -> bool:
        """
        Whether an altitude measured on this side lies below sea level.

        Returns
        -------
        bool
            True for `BELOW_SEA_LEVEL`.
        """
        match self:
            case AltitudeReference.ABOVE_SEA_LEVEL:
                return False
            case AltitudeReference.BELOW_SEA_LEVEL:
                return True

    @classmethod
    def from_value(cls, value: ExifValue) -> AltitudeReference:
        """
        Interpret a raw `GPSAltitudeRef` value.

        The tag is a single byte, which Pillow decodes as either `int` or
        one-byte `bytes` depending on the writer.

        Parameters
        ----------
        value : ExifValue
            The tag value.

        Returns
        -------
        AltitudeReference
            The reference.

        Raises
        ------
        TypeError
            If the value is neither an integer nor a single byte.
        ValueError
            If the value is neither 0 nor 1.
        """
        match value:
            case int():
                return cls(value)
            case bytes() if len(value) == 1:
                return cls(value[0])
            case _:
                raise TypeError(
                    f"Tag GPSAltitudeRef holds {type(value).__name__}, expected a single byte"
                )

from typing import cast

from PIL.TiffImagePlugin import IFDRational

from .value import ExifValue


class ExifValueNormalizer:
    """
    Convert the raw values Pillow decodes into `ExifValue`.

    Rationals become `float` (NaN for a zero denominator), ASCII strings lose
    their trailing NUL padding, and sequences become tuples, so every value
    exposed by this package is immutable and free of Pillow-specific types.
    """

    @staticmethod
    def normalize(raw_value: object) -> ExifValue:
        """
        Normalize one raw value decoded by Pillow.

        Parameters
        ----------
        raw_value : object
            The value as returned by `PIL.Image.Exif`.

        Returns
        -------
        ExifValue
            The normalized value.

        Raises
        ------
        TypeError
            If the value has a type Exif does not define.
        """
        match raw_value:
            case IFDRational():
                return float(raw_value)
            case bool():
                return int(raw_value)
            case str():
                return raw_value.rstrip("\x00").strip()
            case int() | float() | bytes():
                return raw_value
            case bytearray():
                return bytes(raw_value)
            case tuple() | list():
                items = cast("tuple[object, ...] | list[object]", raw_value)
                return tuple(ExifValueNormalizer.normalize(item) for item in items)
            case _:
                raise TypeError(f"Unsupported Exif value type: {type(raw_value).__name__}")

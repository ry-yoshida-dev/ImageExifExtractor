import math

from .value import ExifValue, JsonValue


class ExifJsonConverter:
    """
    Convert `ExifValue` into values `json.dumps` serializes as standard JSON.

    Bytes holding printable ASCII (e.g. `ExifVersion`) become that text and
    other bytes become a hexadecimal string. NaN, which an undefined rational
    normalizes to, becomes `None`, since JSON has no NaN.
    """

    @staticmethod
    def convert(value: ExifValue) -> JsonValue:
        """
        Convert one normalized Exif value.

        Parameters
        ----------
        value : ExifValue
            The value to convert.

        Returns
        -------
        JsonValue
            The JSON-compatible representation.
        """
        match value:
            case float() if math.isnan(value):
                return None
            case str() | int() | float():
                return value
            case bytes() if value.isascii() and value.decode("ascii").isprintable():
                return value.decode("ascii")
            case bytes():
                return value.hex()
            case tuple():
                return [ExifJsonConverter.convert(item) for item in value]

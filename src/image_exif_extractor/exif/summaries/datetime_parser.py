from datetime import datetime
from typing import ClassVar


class ExifDateTimeParser:
    """
    Parse the Exif `YYYY:MM:DD HH:MM:SS` date-time format.

    Exif stores the time zone offset and the sub-second fraction in separate
    tags, so both are combined into the parsed `datetime` when present.
    """

    DATE_TIME_FORMAT: ClassVar[str] = "%Y:%m:%d %H:%M:%S"
    OFFSET_FORMAT: ClassVar[str] = "%z"
    MICROSECOND_DIGIT_COUNT: ClassVar[int] = 6

    @staticmethod
    def parse(
        date_time_text: str,
        offset_text: str | None,
        subsecond_text: str | None,
    ) -> datetime | None:
        """
        Parse one Exif date-time.

        Parameters
        ----------
        date_time_text : str
            The date-time, e.g. `2024:05:01 12:34:56`.
        offset_text : str | None
            The offset from UTC, e.g. `+09:00`. The result is naive without it,
            or when it is marked unknown by blank fields such as `   :  `.
        subsecond_text : str | None
            The fractional digits of the second, e.g. `123` for 0.123 seconds.

        Returns
        -------
        datetime | None
            The parsed date-time, or None when it is marked unknown by blank
            or all-zero fields as the Exif specification allows.

        Raises
        ------
        ValueError
            If any given text does not follow the Exif format.
        """
        if not date_time_text.strip(" :0"):
            return None

        parsed = datetime.strptime(date_time_text, ExifDateTimeParser.DATE_TIME_FORMAT)

        if subsecond_text is not None:
            if not subsecond_text.isdigit():
                raise ValueError(f"Sub-second text must be digits, given: {subsecond_text}")
            microsecond_text = subsecond_text[: ExifDateTimeParser.MICROSECOND_DIGIT_COUNT]
            parsed = parsed.replace(
                microsecond=int(
                    microsecond_text.ljust(ExifDateTimeParser.MICROSECOND_DIGIT_COUNT, "0")
                )
            )

        if offset_text is not None and offset_text.strip(" :"):
            parsed = parsed.replace(
                tzinfo=datetime.strptime(offset_text, ExifDateTimeParser.OFFSET_FORMAT).tzinfo
            )

        return parsed

from datetime import datetime, timedelta, timezone

import pytest

from image_exif_extractor.exif.summaries import ExifDateTimeParser


class TestExifDateTimeParser:
    def test_parses_naive_date_time(self) -> None:
        parsed = ExifDateTimeParser.parse("2024:05:01 12:34:56", None, None)

        assert parsed == datetime(2024, 5, 1, 12, 34, 56)

    def test_combines_offset_and_subsecond(self) -> None:
        parsed = ExifDateTimeParser.parse("2024:05:01 12:34:56", "-05:30", "1234567")

        assert parsed == datetime(
            2024, 5, 1, 12, 34, 56, 123456, tzinfo=timezone(-timedelta(hours=5, minutes=30))
        )

    @pytest.mark.parametrize("offset_text", ["   :  ", ""])
    def test_treats_unknown_offset_as_naive(self, offset_text: str) -> None:
        parsed = ExifDateTimeParser.parse("2024:05:01 12:34:56", offset_text, None)

        assert parsed == datetime(2024, 5, 1, 12, 34, 56)

    @pytest.mark.parametrize("text", ["0000:00:00 00:00:00", "    :  :     :  :  "])
    def test_treats_unknown_as_absent(self, text: str) -> None:
        assert ExifDateTimeParser.parse(text, None, None) is None

    @pytest.mark.parametrize(
        ("date_time_text", "offset_text", "subsecond_text"),
        [
            ("2024-05-01 12:34:56", None, None),
            ("2024:05:01 12:34:56", "JST", None),
            ("2024:05:01 12:34:56", None, "1a"),
        ],
    )
    def test_rejects_malformed_text(
        self,
        date_time_text: str,
        offset_text: str | None,
        subsecond_text: str | None,
    ) -> None:
        with pytest.raises(ValueError):
            ExifDateTimeParser.parse(date_time_text, offset_text, subsecond_text)

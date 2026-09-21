import pytest

from image_exif_extractor.exif.tags import ExifJsonConverter, ExifValue, JsonValue


class TestExifJsonConverter:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            ("Canon", "Canon"),
            (400, 400),
            (0.25, 0.25),
            (float("nan"), None),
            (b"0232", "0232"),
            (b"\x00\x01\xff", "0001ff"),
            ((1, (0.5, b"\x02")), [1, [0.5, "02"]]),
        ],
    )
    def test_converts_value(self, value: ExifValue, expected: JsonValue) -> None:
        assert ExifJsonConverter.convert(value) == expected

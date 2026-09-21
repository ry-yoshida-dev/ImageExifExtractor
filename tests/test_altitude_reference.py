import pytest

from image_exif_extractor import AltitudeReference
from image_exif_extractor.exif.tags import ExifValue


class TestAltitudeReference:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0, AltitudeReference.ABOVE_SEA_LEVEL),
            (1, AltitudeReference.BELOW_SEA_LEVEL),
            (b"\x01", AltitudeReference.BELOW_SEA_LEVEL),
        ],
    )
    def test_reads_value(self, value: ExifValue, expected: AltitudeReference) -> None:
        assert AltitudeReference.from_value(value) is expected

    def test_describes_side_of_sea_level(self) -> None:
        assert not AltitudeReference.ABOVE_SEA_LEVEL.is_below_sea_level
        assert AltitudeReference.BELOW_SEA_LEVEL.is_below_sea_level

    @pytest.mark.parametrize("value", ["0", b"\x00\x01", 1.0])
    def test_rejects_wrong_type(self, value: ExifValue) -> None:
        with pytest.raises(TypeError, match="GPSAltitudeRef"):
            AltitudeReference.from_value(value)

    def test_rejects_undefined_value(self) -> None:
        with pytest.raises(ValueError):
            AltitudeReference.from_value(2)

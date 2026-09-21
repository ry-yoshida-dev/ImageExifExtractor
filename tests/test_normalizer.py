import math

import pytest
from PIL.TiffImagePlugin import IFDRational

from image_exif_extractor.exif.tags import ExifValueNormalizer


class TestExifValueNormalizer:
    def test_converts_rational_to_float(self) -> None:
        assert ExifValueNormalizer.normalize(IFDRational(1, 4)) == 0.25

    def test_converts_zero_denominator_to_nan(self) -> None:
        normalized = ExifValueNormalizer.normalize(IFDRational(1, 0))

        assert isinstance(normalized, float)
        assert math.isnan(normalized)

    def test_strips_text_padding(self) -> None:
        assert ExifValueNormalizer.normalize(" Canon\x00\x00") == "Canon"

    def test_converts_sequences_recursively(self) -> None:
        normalized = ExifValueNormalizer.normalize([IFDRational(1, 2), [3, bytearray(b"a")]])

        assert normalized == (0.5, (3, b"a"))

    def test_rejects_unsupported_type(self) -> None:
        with pytest.raises(TypeError, match="dict"):
            ExifValueNormalizer.normalize({1: 2})

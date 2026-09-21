import pytest

from image_exif_extractor import Orientation


class TestOrientation:
    @pytest.mark.parametrize(
        ("orientation", "degrees", "is_mirrored"),
        [
            (Orientation.NORMAL, 0, False),
            (Orientation.MIRROR_HORIZONTAL, 0, True),
            (Orientation.ROTATE_180, 180, False),
            (Orientation.MIRROR_VERTICAL, 180, True),
            (Orientation.MIRROR_HORIZONTAL_ROTATE_270, 270, True),
            (Orientation.ROTATE_90, 90, False),
            (Orientation.MIRROR_HORIZONTAL_ROTATE_90, 90, True),
            (Orientation.ROTATE_270, 270, False),
        ],
    )
    def test_describes_transformation(
        self, orientation: Orientation, degrees: int, is_mirrored: bool
    ) -> None:
        assert orientation.clockwise_rotation_degrees == degrees
        assert orientation.is_mirrored is is_mirrored

    def test_rejects_undefined_value(self) -> None:
        with pytest.raises(ValueError):
            Orientation(9)

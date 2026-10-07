from pathlib import Path

import pytest
from geo_coordinate import NorthReference
from PIL.ExifTags import GPS

from image_exif_extractor import ExifEntry, ExifIFD, ExifMetadata, ExifValue, GpsBearingKind


def metadata_of(tags: dict[int, ExifValue]) -> ExifMetadata:
    return ExifMetadata(
        path=Path("synthetic.jpg"),
        entries=tuple(
            ExifEntry(ifd=ExifIFD.GPS, tag_id=tag_id, value=value) for tag_id, value in tags.items()
        ),
    )


class TestGpsBearing:
    @pytest.mark.parametrize(
        ("letter", "reference"), [("T", NorthReference.TRUE), ("M", NorthReference.MAGNETIC)]
    )
    def test_reads_image_direction_with_its_north(
        self, letter: str, reference: NorthReference
    ) -> None:
        metadata = metadata_of({GPS.GPSImgDirectionRef: letter, GPS.GPSImgDirection: 90.5})

        direction = metadata.image_direction

        assert direction is not None
        assert direction.degree == pytest.approx([90.5])
        assert direction.reference is reference

    def test_reads_direction_without_reference_as_true_north(self) -> None:
        direction = metadata_of({GPS.GPSImgDirection: 12.0}).image_direction

        assert direction is not None
        assert direction.reference is NorthReference.TRUE

    def test_reads_a_full_turn_as_north(self) -> None:
        direction = metadata_of({GPS.GPSImgDirection: 360.0}).image_direction

        assert direction is not None
        assert direction.degree == pytest.approx([0.0])

    @pytest.mark.parametrize("tags", [{}, {GPS.GPSImgDirection: float("nan")}])
    def test_reads_absent_or_undefined_direction_as_none(self, tags: dict[int, ExifValue]) -> None:
        assert metadata_of(tags).image_direction is None

    def test_rejects_unknown_reference(self) -> None:
        metadata = metadata_of({GPS.GPSImgDirectionRef: "X", GPS.GPSImgDirection: 1.0})

        with pytest.raises(ValueError):
            _ = metadata.image_direction

    @pytest.mark.parametrize(
        ("kind", "value_tag", "reference_tag"),
        [
            (GpsBearingKind.TRACK, GPS.GPSTrack, GPS.GPSTrackRef),
            (GpsBearingKind.DESTINATION_BEARING, GPS.GPSDestBearing, GPS.GPSDestBearingRef),
        ],
    )
    def test_reads_other_directions(
        self, kind: GpsBearingKind, value_tag: int, reference_tag: int
    ) -> None:
        metadata = metadata_of({reference_tag: "M", value_tag: 45.0})

        bearing = metadata.gps_bearing(kind)

        assert bearing is not None
        assert bearing.degree == pytest.approx([45.0])
        assert bearing.reference is NorthReference.MAGNETIC
        assert metadata.image_direction is None

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from PIL.ExifTags import GPS, Base

from image_exif_extractor import ExifEntry, ExifExtractor, ExifIFD, ExifMetadata, Orientation


class TestExifMetadata:
    def test_interprets_camera(self, exif_image_path: Path) -> None:
        camera = ExifExtractor().extract(exif_image_path).camera

        assert camera.make == "Canon"
        assert camera.model == "EOS R5"
        assert camera.lens_model == "RF50mm F1.8 STM"
        assert camera.lens_make is None
        assert camera.software == "Firmware 1.8.1"

    def test_interprets_capture_settings(self, exif_image_path: Path) -> None:
        settings = ExifExtractor().extract(exif_image_path).capture_settings

        assert settings.exposure_time == pytest.approx(1 / 250)
        assert settings.f_number == pytest.approx(2.8)
        assert settings.iso == 400
        assert settings.focal_length == pytest.approx(50)
        assert settings.focal_length_in_35mm_film == 50
        assert settings.captured_at == datetime(
            2024, 5, 1, 12, 34, 56, 250000, tzinfo=timezone(timedelta(hours=9))
        )

    def test_interprets_gps_coordinate(self, exif_image_path: Path) -> None:
        coordinate = ExifExtractor().extract(exif_image_path).gps_coordinate

        assert coordinate is not None
        assert len(coordinate) == 1
        assert coordinate.latitude.degree == pytest.approx([35.6751])
        assert coordinate.longitude.degree == pytest.approx([-139.75])
        assert coordinate.altitude is not None
        assert coordinate.altitude.meter == pytest.approx([-40.5])

    def test_interprets_orientation(self, exif_image_path: Path) -> None:
        orientation = ExifExtractor().extract(exif_image_path).orientation

        assert orientation is Orientation.ROTATE_90
        assert orientation.is_dimension_swapped

    def test_interprets_absent_fields_as_none(self, plain_image_path: Path) -> None:
        metadata = ExifExtractor().extract(plain_image_path)

        assert metadata.camera.make is None
        assert metadata.capture_settings.captured_at is None
        assert metadata.gps_coordinate is None
        assert metadata.orientation is None

    def test_falls_back_to_modification_time(self) -> None:
        metadata = ExifMetadata(
            path=Path("image.jpg"),
            entries=(ExifEntry(ExifIFD.BASE, Base.DateTime, "2024:05:02 08:00:00"),),
        )

        assert metadata.capture_settings.captured_at == datetime(2024, 5, 2, 8, 0, 0)

    def test_treats_undefined_rational_as_absent(self) -> None:
        metadata = ExifMetadata(
            path=Path("image.jpg"),
            entries=(ExifEntry(ExifIFD.EXIF, Base.FNumber, float("nan")),),
        )

        assert metadata.find_number(ExifIFD.EXIF, Base.FNumber) is None
        assert metadata.capture_settings.f_number is None

    def test_caches_interpreted_fields(self, exif_image_path: Path) -> None:
        metadata = ExifExtractor().extract(exif_image_path)

        assert metadata.capture_settings is metadata.capture_settings
        assert metadata.gps_coordinate is metadata.gps_coordinate

    def test_is_truthy_without_entries(self, plain_image_path: Path) -> None:
        metadata = ExifExtractor().extract(plain_image_path)

        assert metadata.is_empty
        assert metadata

    def test_reads_iso_stored_as_sequence(self) -> None:
        metadata = ExifMetadata(
            path=Path("image.jpg"),
            entries=(ExifEntry(ExifIFD.EXIF, Base.ISOSpeedRatings, (800, 0)),),
        )

        assert metadata.capture_settings.iso == 800

    def test_treats_undefined_gps_as_absent(self) -> None:
        nan = float("nan")
        metadata = ExifMetadata(
            path=Path("image.jpg"),
            entries=(
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitudeRef, "N"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitude, (nan, nan, nan)),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitudeRef, "E"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitude, (nan, nan, nan)),
            ),
        )

        assert metadata.gps_coordinate is None

    def test_rejects_gps_without_reference(self) -> None:
        metadata = ExifMetadata(
            path=Path("image.jpg"),
            entries=(
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitude, (35.0, 0.0, 0.0)),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitudeRef, "E"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitude, (139.0, 0.0, 0.0)),
            ),
        )

        with pytest.raises(ValueError, match="GPSLatitudeRef"):
            _ = metadata.gps_coordinate

    def test_reads_gps_without_altitude(self) -> None:
        metadata = ExifMetadata(
            path=Path("image.jpg"),
            entries=(
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitudeRef, "S"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitude, 33.8688),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitudeRef, "E"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitude, (151.0, 12.0, 32.0)),
            ),
        )

        coordinate = metadata.gps_coordinate

        assert coordinate is not None
        assert coordinate.latitude.degree == pytest.approx([-33.8688])
        assert coordinate.longitude.degree == pytest.approx([151.2089], abs=1e-4)
        assert coordinate.altitude is None

    def test_reads_altitude_without_reference_as_above_sea_level(self) -> None:
        metadata = ExifMetadata(
            path=Path("image.jpg"),
            entries=(
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitudeRef, "N"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitude, 35.0),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitudeRef, "E"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitude, 139.0),
                ExifEntry(ExifIFD.GPS, GPS.GPSAltitude, 12.5),
            ),
        )

        coordinate = metadata.gps_coordinate

        assert coordinate is not None
        assert coordinate.altitude is not None
        assert coordinate.altitude.meter == pytest.approx([12.5])

    def test_carries_non_canonical_components(self) -> None:
        metadata = ExifMetadata(
            path=Path("image.jpg"),
            entries=(
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitudeRef, "N"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitude, (35.0, 40.506, 0.0)),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitudeRef, "W"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitude, (139.0, 44.0, 60.0)),
            ),
        )

        coordinate = metadata.gps_coordinate

        assert coordinate is not None
        latitude = coordinate.latitude.degrees_minutes_seconds
        assert (latitude.degrees[0], latitude.minutes[0]) == (35, 40)
        assert latitude.seconds[0] == pytest.approx(30.36)
        assert coordinate.longitude.degree == pytest.approx([-139.75])

    def test_rejects_negative_gps_component(self) -> None:
        metadata = ExifMetadata(
            path=Path("image.jpg"),
            entries=(
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitudeRef, "N"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLatitude, (-35.0, 0.0, 0.0)),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitudeRef, "E"),
                ExifEntry(ExifIFD.GPS, GPS.GPSLongitude, (139.0, 0.0, 0.0)),
            ),
        )

        with pytest.raises(ValueError, match="non-negative"):
            _ = metadata.gps_coordinate

    def test_rejects_text_tag_with_wrong_type(self) -> None:
        metadata = ExifMetadata(
            path=Path("image.jpg"),
            entries=(ExifEntry(ExifIFD.BASE, Base.Make, b"Canon"),),
        )

        with pytest.raises(TypeError, match="Make"):
            _ = metadata.camera

    def test_serializes_to_json(self, exif_image_path: Path) -> None:
        document = ExifExtractor().extract(exif_image_path).to_json_dict()

        decoded = json.loads(json.dumps(document, allow_nan=False))
        assert decoded["path"] == str(exif_image_path)
        assert decoded["ifds"]["base"]["Make"] == "Canon"
        assert decoded["ifds"]["exif"]["ExifVersion"] == "0232"
        assert decoded["ifds"]["gps"]["GPSAltitudeRef"] == "01"

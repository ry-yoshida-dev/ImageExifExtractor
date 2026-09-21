from pathlib import Path

import pytest
from PIL import UnidentifiedImageError
from PIL.ExifTags import GPS, Base

from image_exif_extractor import ExifExtractor, ExifIFD


class TestExifExtractor:
    def test_extracts_every_directory(self, exif_image_path: Path) -> None:
        metadata = ExifExtractor().extract(exif_image_path)

        assert metadata.path == exif_image_path
        assert metadata.find_value(ExifIFD.BASE, Base.Make) == "Canon"
        assert metadata.find_value(ExifIFD.EXIF, Base.ISOSpeedRatings) == 400
        assert metadata.find_value(ExifIFD.GPS, GPS.GPSLatitudeRef) == "N"

    def test_strips_nul_padding(self, exif_image_path: Path) -> None:
        metadata = ExifExtractor().extract(exif_image_path)

        assert metadata.find_value(ExifIFD.BASE, Base.Model) == "EOS R5"

    def test_normalizes_rationals_to_float(self, exif_image_path: Path) -> None:
        metadata = ExifExtractor().extract(exif_image_path)

        assert metadata.find_value(ExifIFD.EXIF, Base.ExposureTime) == pytest.approx(0.004)
        assert metadata.find_value(ExifIFD.GPS, GPS.GPSLatitude) == pytest.approx((35, 40, 30.36))

    def test_skips_pointer_tags(self, exif_image_path: Path) -> None:
        metadata = ExifExtractor().extract(exif_image_path)

        tag_ids = {entry.tag_id for entry in metadata.entries_in(ExifIFD.BASE)}
        assert tag_ids.isdisjoint(ExifIFD.pointer_tag_ids())

    def test_excludes_maker_note_by_default(self, exif_image_path: Path) -> None:
        metadata = ExifExtractor().extract(exif_image_path)

        assert metadata.find(ExifIFD.EXIF, Base.MakerNote) is None

    def test_includes_maker_note_on_request(self, exif_image_path: Path) -> None:
        metadata = ExifExtractor(is_maker_note_included=True).extract(exif_image_path)

        assert metadata.find_value(ExifIFD.EXIF, Base.MakerNote) == b"\x01\x02\x03"

    def test_restricts_to_selected_directories(self, exif_image_path: Path) -> None:
        metadata = ExifExtractor(ifds=[ExifIFD.GPS]).extract(exif_image_path)

        assert {entry.ifd for entry in metadata.entries} == {ExifIFD.GPS}

    def test_returns_empty_metadata_without_exif(self, plain_image_path: Path) -> None:
        metadata = ExifExtractor().extract(plain_image_path)

        assert metadata.is_empty

    def test_extract_all_preserves_order(
        self, exif_image_path: Path, plain_image_path: Path
    ) -> None:
        paths = [plain_image_path, exif_image_path]

        metadata_list = list(ExifExtractor().extract_all(paths))

        assert [metadata.path for metadata in metadata_list] == paths

    def test_rejects_empty_directory_selection(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            ExifExtractor(ifds=[])

    def test_rejects_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            ExifExtractor().extract(tmp_path / "missing.jpg")

    def test_rejects_non_image_file(self, tmp_path: Path) -> None:
        path = tmp_path / "text.jpg"
        path.write_text("not an image")

        with pytest.raises(UnidentifiedImageError):
            ExifExtractor().extract(path)

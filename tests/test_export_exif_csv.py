import csv
import io
from pathlib import Path

import pytest
from PIL import Image

from utils.export_exif_csv import ExifCsvExporter


class TestExifCsvExporter:
    @pytest.fixture
    def image_directory(self, exif_image_path: Path, plain_image_path: Path) -> Path:
        directory = exif_image_path.parent
        (directory / "notes.txt").write_text("not an image")
        (directory / "broken.jpg").write_text("not an image")
        nested_directory = directory / "nested"
        nested_directory.mkdir()
        Image.new("RGB", (8, 8)).save(nested_directory / "inner.png")
        return directory

    def export_rows(self, exporter: ExifCsvExporter, directory: Path) -> list[dict[str, str]]:
        output = io.StringIO(newline="")
        exporter.export(directory, output)
        output.seek(0)
        return list(csv.DictReader(output))

    def test_writes_selected_tags(self, image_directory: Path) -> None:
        exporter = ExifCsvExporter(tag_names=["make", "FNumber", "GPSLatitude", "ExifVersion"])

        rows = {row["file"]: row for row in self.export_rows(exporter, image_directory)}

        assert list(rows) == ["broken.jpg", "exif.jpg", "plain.png"]
        assert rows["exif.jpg"]["Make"] == "Canon"
        assert float(rows["exif.jpg"]["FNumber"]) == pytest.approx(2.8)
        assert rows["exif.jpg"]["GPSLatitude"] == "[35.0, 40.0, 30.36]"
        assert rows["exif.jpg"]["ExifVersion"] == "0232"
        assert rows["plain.png"]["Make"] == ""

    def test_records_unreadable_file(self, image_directory: Path) -> None:
        exporter = ExifCsvExporter(tag_names=["Make"])
        output = io.StringIO(newline="")

        failed_count = exporter.export(image_directory, output)

        output.seek(0)
        rows = {row["file"]: row for row in csv.DictReader(output)}
        assert failed_count == 1
        assert rows["broken.jpg"]["error"].startswith("UnidentifiedImageError")
        assert rows["exif.jpg"]["error"] == ""

    def test_adds_gps_columns(self, image_directory: Path) -> None:
        exporter = ExifCsvExporter(tag_names=[], is_gps_included=True)

        rows = {row["file"]: row for row in self.export_rows(exporter, image_directory)}

        assert float(rows["exif.jpg"]["latitude"]) == pytest.approx(35.6751)
        assert float(rows["exif.jpg"]["longitude"]) == pytest.approx(-139.75)
        assert float(rows["exif.jpg"]["altitude"]) == pytest.approx(-40.5)
        assert rows["plain.png"]["latitude"] == ""

    def test_scans_sub_directories_on_request(self, image_directory: Path) -> None:
        exporter = ExifCsvExporter(tag_names=["Make"], is_recursive=True)

        files = [row["file"] for row in self.export_rows(exporter, image_directory)]

        assert "nested/inner.png" in files

    def test_rejects_unknown_tag(self) -> None:
        with pytest.raises(ValueError, match="NoSuchTag"):
            ExifCsvExporter(tag_names=["NoSuchTag"])

    def test_rejects_empty_selection(self) -> None:
        with pytest.raises(ValueError, match="at least one"):
            ExifCsvExporter(tag_names=[])

    def test_rejects_missing_directory(self, tmp_path: Path) -> None:
        with pytest.raises(NotADirectoryError):
            ExifCsvExporter().image_paths_in(tmp_path / "missing")

    def test_writes_csv_file_from_command_line(self, image_directory: Path, tmp_path: Path) -> None:
        output_path = tmp_path / "out" / "exif.csv"
        output_path.parent.mkdir()

        status = ExifCsvExporter.run_command_line(
            [str(image_directory), "--output", str(output_path), "--tag", "Model", "--gps"]
        )

        with output_path.open(newline="", encoding="utf-8-sig") as output:
            rows = list(csv.DictReader(output))
        assert status == 1
        assert rows[0].keys() == {"file", "Model", "latitude", "longitude", "altitude", "error"}

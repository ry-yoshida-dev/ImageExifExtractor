import json
from pathlib import Path

import pytest

from utils.print_exif_json import ExifJsonPrinter


class TestExifJsonPrinter:
    def test_prints_json_array(
        self, exif_image_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        status = ExifJsonPrinter().run([str(exif_image_path)])

        documents = json.loads(capsys.readouterr().out)
        assert status == 0
        assert documents[0]["ifds"]["base"]["Make"] == "Canon"

    def test_restricts_to_selected_directories(
        self, exif_image_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        ExifJsonPrinter().run([str(exif_image_path), "--ifd", "gps"])

        documents = json.loads(capsys.readouterr().out)
        assert list(documents[0]["ifds"]) == ["gps"]

    def test_rejects_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(SystemExit):
            ExifJsonPrinter().run([str(tmp_path / "missing.jpg")])

    def test_reports_unreadable_file_and_continues(
        self, exif_image_path: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        broken_path = tmp_path / "broken.jpg"
        broken_path.write_text("not an image")

        status = ExifJsonPrinter().run([str(broken_path), str(exif_image_path)])

        captured = capsys.readouterr()
        documents = json.loads(captured.out)
        assert status == 1
        assert [document["path"] for document in documents] == [str(exif_image_path)]
        assert "broken.jpg" in captured.err

    def test_rejects_negative_indent(self, exif_image_path: Path) -> None:
        with pytest.raises(SystemExit):
            ExifJsonPrinter().run([str(exif_image_path), "--indent", "-1"])

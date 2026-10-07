import io
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Final

import numpy as np
import pytest
from geo_coordinate import Altitude, Bearing, GeoCoordinate, NorthReference
from PIL import ExifTags, Image
from PIL.ExifTags import GPS, Base
from units import Length, LengthUnit

from image_exif_extractor import ExifExtractor, ExifIFD, ExifUpdate, ExifWriter
from image_exif_extractor.writing import (
    ByteOrder,
    JpegFile,
    TiffBlock,
    TiffDirectory,
    TiffFieldType,
)

THUMBNAIL_OFFSET_TAG: Final[int] = 0x0201
THUMBNAIL_LENGTH_TAG: Final[int] = 0x0202
COORDINATE_TOLERANCE: Final[float] = 1e-6
TOKYO_STATION: Final[GeoCoordinate] = GeoCoordinate.from_degrees(35.681236, 139.767125)
MAKER_NOTE: Final[bytes] = b"maker-note-bytes"


def jpeg_bytes(exif: Image.Exif | None = None) -> bytes:
    buffer = io.BytesIO()
    image = Image.effect_noise((64, 48), 64).convert("RGB")
    if exif is None:
        image.save(buffer, format="JPEG", quality=90)
    else:
        image.save(buffer, format="JPEG", quality=90, exif=exif)
    return buffer.getvalue()


def thumbnail_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 6), "red").save(buffer, format="JPEG")
    return buffer.getvalue()


def with_thumbnail(data: bytes, thumbnail: bytes) -> bytes:
    """
    Add an IFD1 holding a thumbnail, as cameras write one after IFD0.

    Parameters
    ----------
    data : bytes
        A JPEG file with an Exif block.
    thumbnail : bytes
        The JPEG of the thumbnail.

    Returns
    -------
    bytes
        The file whose IFD0 is followed by the thumbnail directory.
    """
    jpeg = JpegFile.parse(data)
    tiff = jpeg.exif_tiff
    assert tiff is not None
    block = TiffBlock(tiff)
    stored = block.entry(THUMBNAIL_OFFSET_TAG, TiffFieldType.BYTE, len(thumbnail), thumbnail)
    thumbnail_offset = block.pointer_of(TiffDirectory(entries=(stored,)), THUMBNAIL_OFFSET_TAG)
    assert thumbnail_offset is not None
    ifd1 = (
        TiffDirectory(entries=())
        .with_entry(block.pointer_entry(THUMBNAIL_OFFSET_TAG, thumbnail_offset))
        .with_entry(block.pointer_entry(THUMBNAIL_LENGTH_TAG, len(thumbnail)))
    )
    ifd0 = block.read_directory(block.ifd0_offset)
    linked = TiffDirectory(entries=ifd0.entries, next_offset=block.append_directory(ifd1))
    block.set_ifd0_offset(block.append_directory(linked))
    return jpeg.with_exif_tiff(block.to_bytes()).to_bytes()


def thumbnail_of(data: bytes) -> bytes:
    tiff = JpegFile.parse(data).exif_tiff
    assert tiff is not None
    block = TiffBlock(tiff)
    ifd1 = block.read_directory(block.read_directory(block.ifd0_offset).next_offset)
    offset = block.pointer_of(ifd1, THUMBNAIL_OFFSET_TAG)
    length = block.pointer_of(ifd1, THUMBNAIL_LENGTH_TAG)
    assert offset is not None
    assert length is not None
    return tiff[offset : offset + length]


@pytest.fixture
def tagged_jpeg(tmp_path: Path) -> Path:
    exif = Image.Exif()
    exif[Base.Make] = "Canon"
    exif[Base.Model] = "EOS R5"
    exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
    exif_ifd[Base.MakerNote] = MAKER_NOTE
    exif_ifd[Base.ISOSpeedRatings] = 400
    exif_ifd[Base.DateTimeOriginal] = "2020:01:01 00:00:00"
    exif_ifd[Base.SubsecTimeOriginal] = "25"
    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps_ifd[GPS.GPSLatitudeRef] = "N"
    gps_ifd[GPS.GPSLatitude] = (1.0, 0.0, 0.0)
    gps_ifd[GPS.GPSLongitudeRef] = "E"
    gps_ifd[GPS.GPSLongitude] = (1.0, 0.0, 0.0)
    gps_ifd[GPS.GPSAltitudeRef] = b"\x00"
    gps_ifd[GPS.GPSAltitude] = 120.0
    gps_ifd[GPS.GPSMapDatum] = "WGS-84"
    path = tmp_path / "tagged.jpg"
    path.write_bytes(with_thumbnail(jpeg_bytes(exif), thumbnail_bytes()))
    return path


class TestExifWriter:
    def test_writes_location_and_direction(self, tagged_jpeg: Path, tmp_path: Path) -> None:
        destination = tmp_path / "updated.jpg"
        update = ExifUpdate(
            location=TOKYO_STATION,
            image_direction=Bearing.from_degrees(123.45, NorthReference.MAGNETIC),
        )

        written = ExifWriter().write(tagged_jpeg, update, destination)

        metadata = ExifExtractor().extract(written)
        coordinate = metadata.gps_coordinate
        assert written == destination
        assert coordinate is not None
        assert coordinate.latitude.degree == pytest.approx([35.681236], abs=COORDINATE_TOLERANCE)
        assert coordinate.longitude.degree == pytest.approx([139.767125], abs=COORDINATE_TOLERANCE)
        direction = metadata.image_direction
        assert direction is not None
        assert direction.degree == pytest.approx([123.45])
        assert direction.reference is NorthReference.MAGNETIC

    def test_keeps_pixels_and_other_segments_byte_for_byte(
        self, tagged_jpeg: Path, tmp_path: Path
    ) -> None:
        original = JpegFile.parse(tagged_jpeg.read_bytes())

        written = ExifWriter().write(
            tagged_jpeg, ExifUpdate(location=TOKYO_STATION), tmp_path / "updated.jpg"
        )

        updated = JpegFile.parse(written.read_bytes())
        assert updated.image_data == original.image_data
        assert [segment for segment in updated.segments if not segment.is_exif] == [
            segment for segment in original.segments if not segment.is_exif
        ]
        with Image.open(tagged_jpeg) as before, Image.open(written) as after:
            assert np.array_equal(np.asarray(before), np.asarray(after))

    def test_keeps_other_tags_maker_note_and_thumbnail(
        self, tagged_jpeg: Path, tmp_path: Path
    ) -> None:
        written = ExifWriter().write(
            tagged_jpeg,
            ExifUpdate(location=TOKYO_STATION, captured_at=datetime(2024, 5, 1, 12, 0, 0)),
            tmp_path / "updated.jpg",
        )

        metadata = ExifExtractor(is_maker_note_included=True).extract(written)
        assert metadata.find_value(ExifIFD.BASE, Base.Make) == "Canon"
        assert metadata.find_value(ExifIFD.EXIF, Base.ISOSpeedRatings) == 400
        assert metadata.find_value(ExifIFD.EXIF, Base.MakerNote) == MAKER_NOTE
        assert metadata.find_value(ExifIFD.GPS, GPS.GPSMapDatum) == "WGS-84"
        assert thumbnail_of(written.read_bytes()) == thumbnail_bytes()

    def test_replaces_and_removes_the_altitude_of_the_former_location(
        self, tagged_jpeg: Path, tmp_path: Path
    ) -> None:
        below = Altitude.from_magnitude(
            Length(value=np.array([12.34]), unit=LengthUnit.M), np.array([True])
        )
        located = GeoCoordinate.from_degrees(-33.8688, -70.6693, below)

        with_altitude = ExifWriter().write(
            tagged_jpeg, ExifUpdate(location=located), tmp_path / "below.jpg"
        )
        without_altitude = ExifWriter().write(
            tagged_jpeg, ExifUpdate(location=TOKYO_STATION), tmp_path / "unknown.jpg"
        )

        coordinate = ExifExtractor().extract(with_altitude).gps_coordinate
        assert coordinate is not None
        assert coordinate.latitude.degree == pytest.approx([-33.8688], abs=COORDINATE_TOLERANCE)
        assert coordinate.longitude.degree == pytest.approx([-70.6693], abs=COORDINATE_TOLERANCE)
        assert coordinate.altitude is not None
        assert coordinate.altitude.meter == pytest.approx([-12.34])
        replaced = ExifExtractor().extract(without_altitude).gps_coordinate
        assert replaced is not None
        assert replaced.altitude is None

    def test_writes_time_of_capture_with_its_offset(
        self, tagged_jpeg: Path, tmp_path: Path
    ) -> None:
        captured_at = datetime(2024, 5, 1, 12, 34, 56, tzinfo=timezone(timedelta(hours=9)))

        written = ExifWriter().write(
            tagged_jpeg, ExifUpdate(captured_at=captured_at), tmp_path / "dated.jpg"
        )

        metadata = ExifExtractor().extract(written)
        assert metadata.capture_settings.captured_at == captured_at
        assert metadata.find_value(ExifIFD.EXIF, Base.SubsecTimeOriginal) is None
        assert metadata.gps_coordinate is not None

    def test_writes_years_before_1000_with_four_digits(self, tmp_path: Path) -> None:
        written = ExifWriter().write(
            self._plain_jpeg(tmp_path), ExifUpdate(captured_at=datetime(999, 1, 2, 3, 4, 5))
        )

        metadata = ExifExtractor().extract(written)
        assert metadata.find_value(ExifIFD.EXIF, Base.DateTimeOriginal) == "0999:01:02 03:04:05"

    def test_removes_the_offset_of_a_naive_time(self, tmp_path: Path) -> None:
        source = tmp_path / "offset.jpg"
        ExifWriter().write(
            self._plain_jpeg(tmp_path),
            ExifUpdate(captured_at=datetime(2024, 1, 1, tzinfo=UTC)),
            source,
        )

        written = ExifWriter().write(source, ExifUpdate(captured_at=datetime(2024, 1, 2)))

        metadata = ExifExtractor().extract(written)
        assert metadata.find_value(ExifIFD.EXIF, Base.OffsetTimeOriginal) is None
        assert metadata.capture_settings.captured_at == datetime(2024, 1, 2)

    def test_adds_exif_to_a_jpeg_without_any(self, tmp_path: Path) -> None:
        source = self._plain_jpeg(tmp_path)
        assert JpegFile.parse(source.read_bytes()).exif_tiff is None

        written = ExifWriter().write(
            source, ExifUpdate(image_direction=Bearing.from_degrees(270.0))
        )

        direction = ExifExtractor().extract(written).image_direction
        assert written == source
        assert direction is not None
        assert direction.degree == pytest.approx([270.0])
        assert direction.reference is NorthReference.TRUE
        assert list(tmp_path.iterdir()) == [source]

    def test_edits_little_endian_blocks(self, tmp_path: Path) -> None:
        source = tmp_path / "little.jpg"
        plain = JpegFile.parse(self._plain_jpeg(tmp_path).read_bytes())
        source.write_bytes(
            plain.with_exif_tiff(TiffBlock.empty(ByteOrder.LITTLE_ENDIAN).to_bytes()).to_bytes()
        )

        written = ExifWriter().write(source, ExifUpdate(location=TOKYO_STATION))

        tiff = JpegFile.parse(written.read_bytes()).exif_tiff
        assert tiff is not None
        assert TiffBlock(tiff).byte_order is ByteOrder.LITTLE_ENDIAN
        assert ExifExtractor().extract(written).gps_coordinate is not None

    def test_edits_a_file_again(self, tagged_jpeg: Path) -> None:
        writer = ExifWriter()

        writer.write(tagged_jpeg, ExifUpdate(image_direction=Bearing.from_degrees(10.0)))
        writer.write(tagged_jpeg, ExifUpdate(image_direction=Bearing.from_degrees(20.0)))

        metadata = ExifExtractor(is_maker_note_included=True).extract(tagged_jpeg)
        direction = metadata.image_direction
        assert direction is not None
        assert direction.degree == pytest.approx([20.0])
        assert metadata.find_value(ExifIFD.EXIF, Base.MakerNote) == MAKER_NOTE
        assert thumbnail_of(tagged_jpeg.read_bytes()) == thumbnail_bytes()

    def test_rejects_files_other_than_jpeg(self, plain_image_path: Path) -> None:
        with pytest.raises(ValueError, match="Not a JPEG"):
            ExifWriter().write(plain_image_path, ExifUpdate(location=TOKYO_STATION))

    def test_rejects_missing_files(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            ExifWriter().write(tmp_path / "missing.jpg", ExifUpdate(location=TOKYO_STATION))

    def test_rejects_an_update_setting_nothing(self) -> None:
        with pytest.raises(ValueError, match="at least one field"):
            ExifUpdate()

    @staticmethod
    def _plain_jpeg(directory: Path) -> Path:
        path = directory / "plain.jpg"
        path.write_bytes(jpeg_bytes())
        return path

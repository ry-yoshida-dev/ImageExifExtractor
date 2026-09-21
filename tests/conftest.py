from pathlib import Path

import pytest
from PIL import ExifTags, Image
from PIL.ExifTags import GPS, Base
from PIL.TiffImagePlugin import IFDRational


@pytest.fixture
def exif_image_path(tmp_path: Path) -> Path:
    """
    Write a JPEG carrying base, Exif and GPS tags.

    Parameters
    ----------
    tmp_path : Path
        Directory provided by pytest.

    Returns
    -------
    Path
        The written image.
    """
    exif = Image.Exif()
    exif[Base.Make] = "Canon"
    exif[Base.Model] = "EOS R5\x00"
    exif[Base.Software] = "Firmware 1.8.1"
    exif[Base.Orientation] = 6
    exif[Base.DateTime] = "2024:05:02 08:00:00"

    exif_ifd = exif.get_ifd(ExifTags.IFD.Exif)
    exif_ifd[Base.DateTimeOriginal] = "2024:05:01 12:34:56"
    exif_ifd[Base.OffsetTimeOriginal] = "+09:00"
    exif_ifd[Base.SubsecTimeOriginal] = "25"
    exif_ifd[Base.ExposureTime] = IFDRational(1, 250)
    exif_ifd[Base.FNumber] = IFDRational(28, 10)
    exif_ifd[Base.ISOSpeedRatings] = 400
    exif_ifd[Base.FocalLength] = IFDRational(50, 1)
    exif_ifd[Base.FocalLengthIn35mmFilm] = 50
    exif_ifd[Base.LensModel] = "RF50mm F1.8 STM"
    exif_ifd[Base.ExifVersion] = b"0232"
    exif_ifd[Base.MakerNote] = b"\x01\x02\x03"

    gps_ifd = exif.get_ifd(ExifTags.IFD.GPSInfo)
    gps_ifd[GPS.GPSLatitudeRef] = "N"
    gps_ifd[GPS.GPSLatitude] = (IFDRational(35), IFDRational(40), IFDRational(3036, 100))
    gps_ifd[GPS.GPSLongitudeRef] = "W"
    gps_ifd[GPS.GPSLongitude] = (IFDRational(139), IFDRational(45), IFDRational(0))
    gps_ifd[GPS.GPSAltitudeRef] = b"\x01"
    gps_ifd[GPS.GPSAltitude] = IFDRational(405, 10)

    path = tmp_path / "exif.jpg"
    Image.new("RGB", (8, 8)).save(path, exif=exif)
    return path


@pytest.fixture
def plain_image_path(tmp_path: Path) -> Path:
    """
    Write a PNG carrying no Exif.

    Parameters
    ----------
    tmp_path : Path
        Directory provided by pytest.

    Returns
    -------
    Path
        The written image.
    """
    path = tmp_path / "plain.png"
    Image.new("RGB", (8, 8)).save(path)
    return path

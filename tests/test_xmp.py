import io
from pathlib import Path
from typing import Final

import pytest
from geo_coordinate import NorthReference
from PIL import Image, PngImagePlugin

from image_exif_extractor import ExifExtractor, XmpPacket

DJI_ATTRIBUTES: Final[str] = (
    '<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF '
    + 'xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
    + '<rdf:Description xmlns:drone-dji="http://www.dji.com/drone-dji/1.0/" '
    + 'drone-dji:RelativeAltitude="+60.10" drone-dji:GimbalYawDegree="-87.30" '
    + 'drone-dji:GimbalPitchDegree="-90.00" drone-dji:GimbalRollDegree="+0.00" '
    + 'drone-dji:FlightYawDegree="+92.5"/></rdf:RDF></x:xmpmeta>'
)
DJI_ELEMENTS: Final[str] = (
    '<rdf:Description xmlns:drone-dji="http://www.dji.com/drone-dji/1.0/">'
    + "<drone-dji:RelativeAltitude>-2.5</drone-dji:RelativeAltitude>"
    + "<drone-dji:GimbalYawDegree>180</drone-dji:GimbalYawDegree>"
    + "<drone-dji:GimbalPitchDegree>-45.0</drone-dji:GimbalPitchDegree>"
    + "</rdf:Description>"
)


class TestXmpPacket:
    def test_reads_attribute_properties(self) -> None:
        packet = XmpPacket(text=DJI_ATTRIBUTES)

        assert packet.find_text("drone-dji:GimbalYawDegree") == "-87.30"
        assert packet.find_number("drone-dji:RelativeAltitude") == pytest.approx(60.1)

    def test_reads_element_properties(self) -> None:
        packet = XmpPacket(text=DJI_ELEMENTS)

        assert packet.find_number("drone-dji:RelativeAltitude") == pytest.approx(-2.5)

    def test_reads_absent_properties_as_none(self) -> None:
        assert XmpPacket(text=DJI_ATTRIBUTES).find_number("drone-dji:Missing") is None

    def test_rejects_values_that_are_not_numbers(self) -> None:
        packet = XmpPacket(text='<rdf:Description a:b="north"/>')

        with pytest.raises(ValueError, match="not a number"):
            packet.find_number("a:b")

    def test_rejects_invalid_names(self) -> None:
        with pytest.raises(ValueError, match="Invalid qualified name"):
            XmpPacket(text="").find_text("no colon")


class TestDroneAttitude:
    def test_reads_the_attitude_of_a_dji_photo(self, tmp_path: Path) -> None:
        path = tmp_path / "DJI_0001.JPG"
        buffer = io.BytesIO()
        Image.new("RGB", (8, 8)).save(buffer, format="JPEG", xmp=DJI_ATTRIBUTES.encode())
        path.write_bytes(buffer.getvalue())

        attitude = ExifExtractor().extract(path).drone_attitude

        assert attitude is not None
        assert attitude.relative_altitude.meter == pytest.approx([60.1])
        assert attitude.gimbal_yaw.degree == pytest.approx([272.7])
        assert attitude.gimbal_yaw.reference is NorthReference.TRUE
        assert attitude.gimbal_pitch.degree == pytest.approx([-90.0])
        assert attitude.gimbal_roll is not None
        assert attitude.flight_yaw is not None
        assert attitude.flight_yaw.degree == pytest.approx([92.5])

    def test_reads_an_attitude_below_the_take_off_point(self, tmp_path: Path) -> None:
        path = tmp_path / "DJI_0002.JPG"
        buffer = io.BytesIO()
        Image.new("RGB", (8, 8)).save(buffer, format="JPEG", xmp=DJI_ELEMENTS.encode())
        path.write_bytes(buffer.getvalue())

        attitude = ExifExtractor().extract(path).drone_attitude

        assert attitude is not None
        assert attitude.relative_altitude.meter == pytest.approx([-2.5])
        assert attitude.gimbal_roll is None
        assert attitude.flight_yaw is None

    def test_reads_photos_without_xmp_as_none(self, exif_image_path: Path) -> None:
        metadata = ExifExtractor().extract(exif_image_path)

        assert metadata.xmp is None
        assert metadata.drone_attitude is None

    def test_reads_xmp_without_drone_properties_as_none(self, tmp_path: Path) -> None:
        path = tmp_path / "edited.jpg"
        buffer = io.BytesIO()
        Image.new("RGB", (8, 8)).save(buffer, format="JPEG", xmp=b'<rdf:Description a:b="1"/>')
        path.write_bytes(buffer.getvalue())

        metadata = ExifExtractor().extract(path)

        assert metadata.xmp is not None
        assert metadata.drone_attitude is None

    def test_reads_the_attitude_of_a_png(self, tmp_path: Path) -> None:
        path = tmp_path / "DJI_0003.png"
        info = PngImagePlugin.PngInfo()
        info.add_itxt("XML:com.adobe.xmp", DJI_ATTRIBUTES)
        Image.new("RGB", (8, 8)).save(path, pnginfo=info)

        attitude = ExifExtractor().extract(path).drone_attitude

        assert attitude is not None
        assert attitude.gimbal_yaw.degree == pytest.approx([272.7])

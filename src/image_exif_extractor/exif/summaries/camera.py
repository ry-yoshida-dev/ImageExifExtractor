from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PIL.ExifTags import Base

from ..tags import ExifIFD

if TYPE_CHECKING:
    from ..metadata import ExifMetadata


@dataclass(frozen=True)
class CameraInfo:
    """
    Camera and lens that captured an image.

    Attributes
    ----------
    make : str | None
        Manufacturer of the camera.
    model : str | None
        Model name of the camera.
    lens_make : str | None
        Manufacturer of the lens.
    lens_model : str | None
        Model name of the lens.
    body_serial_number : str | None
        Serial number of the camera body.
    software : str | None
        Firmware or software that wrote the image.
    """

    make: str | None
    model: str | None
    lens_make: str | None
    lens_model: str | None
    body_serial_number: str | None
    software: str | None

    @classmethod
    def from_metadata(cls, metadata: ExifMetadata) -> CameraInfo:
        """
        Read the camera description from extracted metadata.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata to read.

        Returns
        -------
        CameraInfo
            The camera description, with None for each absent field.

        Raises
        ------
        TypeError
            If one of the tags holds a non-text value.
        """
        return cls(
            make=metadata.find_text(ExifIFD.BASE, Base.Make),
            model=metadata.find_text(ExifIFD.BASE, Base.Model),
            lens_make=metadata.find_text(ExifIFD.EXIF, Base.LensMake),
            lens_model=metadata.find_text(ExifIFD.EXIF, Base.LensModel),
            body_serial_number=metadata.find_text(ExifIFD.EXIF, Base.BodySerialNumber),
            software=metadata.find_text(ExifIFD.BASE, Base.Software),
        )

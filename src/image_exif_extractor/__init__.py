"""
Image Exif extractor module for reading Exif metadata from image files.

This module extracts the raw Exif tags of an image into immutable, typed
entries, and interprets common fields such as camera, capture settings,
GPS location, direction and orientation, and reads the attitude of a drone's
camera from XMP. The location, direction and time of
capture can be written back into JPEG files without re-encoding them.
"""

from .exif import (
    AltitudeReference,
    CameraInfo,
    CaptureSettings,
    ExifEntry,
    ExifIFD,
    ExifMetadata,
    ExifValue,
    GpsBearingKind,
    GpsBearingReader,
    GpsCoordinateReader,
    JsonValue,
    Orientation,
)
from .extractor import ExifExtractor
from .heif_support import HeifSupport
from .writing import ExifUpdate, ExifWriter
from .xmp import DroneAttitude, DroneAttitudeReader, XmpPacket

__all__ = [
    "AltitudeReference",
    "CameraInfo",
    "CaptureSettings",
    "DroneAttitude",
    "DroneAttitudeReader",
    "ExifEntry",
    "ExifExtractor",
    "ExifIFD",
    "ExifMetadata",
    "ExifUpdate",
    "ExifValue",
    "ExifWriter",
    "GpsBearingKind",
    "GpsBearingReader",
    "GpsCoordinateReader",
    "HeifSupport",
    "JsonValue",
    "Orientation",
    "XmpPacket",
]

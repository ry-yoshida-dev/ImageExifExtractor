"""
Image Exif extractor module for reading Exif metadata from image files.

This module extracts the raw Exif tags of an image into immutable, typed
entries, and interprets common fields such as camera, capture settings,
GPS location and orientation.
"""

from .exif import (
    AltitudeReference,
    CameraInfo,
    CaptureSettings,
    ExifEntry,
    ExifIFD,
    ExifMetadata,
    ExifValue,
    GpsCoordinateReader,
    JsonValue,
    Orientation,
)
from .extractor import ExifExtractor
from .heif_support import HeifSupport

__all__ = [
    "AltitudeReference",
    "CameraInfo",
    "CaptureSettings",
    "ExifEntry",
    "ExifExtractor",
    "ExifIFD",
    "ExifMetadata",
    "ExifValue",
    "GpsCoordinateReader",
    "HeifSupport",
    "JsonValue",
    "Orientation",
]

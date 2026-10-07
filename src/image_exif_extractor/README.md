# image_exif_extractor

## Overview

Package for extracting the Exif tags of an image into immutable, typed entries, and interpreting the common fields.

## Components

| Component | Description |
|-----------|-------------|
| [extractor.py](./extractor.py) | `ExifExtractor`, the entry point reading the selected directories of image files into `ExifMetadata` |
| [heif_support.py](./heif_support.py) | `HeifSupport`, registering the optional `pillow-heif` opener so HEIF / HEIC images can be read |
| [exif/](./exif/README.md) | `ExifMetadata` returned by `ExifExtractor`, with its raw tags and interpreted fields |
| [xmp/](./xmp/README.md) | `XmpPacket` of the XMP metadata, and the `DroneAttitude` of a drone's camera read from it |

## Values

Pillow's raw values are normalized into `ExifValue`
(`str | int | float | bytes | tuple[ExifValue, ...]`):

| Raw value | Normalized value |
|-----------|------------------|
| Rational | `float`, or NaN for a zero denominator |
| ASCII text | `str` without NUL padding or surrounding whitespace |
| Undefined / byte data | `bytes` |
| Sequence | `tuple` of normalized items |

Pointer tags (`ExifOffset`, `GPSInfo`, `ExifInteroperabilityOffset`) are
skipped, since their directories are extracted as `ExifIFD` entries instead.
`MakerNote` is skipped unless `is_maker_note_included=True`.

## Error Handling

Absent tags read as `None`, and so do numeric tags holding an undefined
rational (a zero denominator). A tag present with the wrong type or a malformed
value raises `TypeError` or `ValueError` when an interpreted field reads it,
rather than being silently dropped.

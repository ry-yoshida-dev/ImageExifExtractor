# tests

## Overview

Pytest suite for `image_exif_extractor`. Fixtures in `conftest.py` write small images with Pillow, so no binary test data is committed.

## Components

| Component | Description |
|-----------|-------------|
| [conftest.py](./conftest.py) | Fixtures writing a JPEG with base, Exif and GPS tags, and a PNG without Exif |
| [test_extractor.py](./test_extractor.py) | Extraction, directory selection, `MakerNote` handling and input validation |
| [test_metadata.py](./test_metadata.py) | Lookups, interpreted fields and JSON export of `ExifMetadata` |
| [test_normalizer.py](./test_normalizer.py) | Normalization of raw Pillow values |
| [test_datetime_parser.py](./test_datetime_parser.py) | Parsing of Exif date-time, offset and sub-second tags |
| [test_orientation.py](./test_orientation.py) | Rotation and mirroring of each `Orientation` |
| [test_print_exif_json.py](./test_print_exif_json.py) | JSON output, unreadable files and argument validation of `utils/print_exif_json.py` |
| [test_altitude_reference.py](./test_altitude_reference.py) | Parsing of `GPSAltitudeRef` values |
| [test_json_converter.py](./test_json_converter.py) | Conversion of normalized values into JSON values |
| [test_heif_support.py](./test_heif_support.py) | Registration of the optional HEIF opener, and the error when the plugin is absent |
| [test_export_exif_csv.py](./test_export_exif_csv.py) | CSV export of a directory by `utils/export_exif_csv.py` |

## Example

```bash
uv run pytest
```

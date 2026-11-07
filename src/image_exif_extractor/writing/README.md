# writing

## Overview

Lossless writing of Exif fields into JPEG files. `ExifWriter` sets the location, the direction the camera faced and the
time of capture of an `ExifUpdate`, replacing only the Exif segment so the image is never re-encoded.

## Components

| Component | Description |
|-----------|-------------|
| [exif_writer.py](./exif_writer.py) | `ExifWriter`, which writes an updated JPEG file, atomically, in place or elsewhere |
| [exif_update.py](./exif_update.py) | `ExifUpdate`, the location, direction and time to set |
| [exif_update_applier.py](./exif_update_applier.py) | `ExifUpdateApplier`, which sets the fields of an update in a TIFF block |
| [jpeg_file.py](./jpeg_file.py) | `JpegFile`, a JPEG file split into header segments and image data |
| [jpeg_segment.py](./jpeg_segment.py) | `JpegSegment`, one marker segment, such as the Exif APP1 |
| [tiff_block.py](./tiff_block.py) | `TiffBlock`, the TIFF structure of Exif, edited by appending directories and values |
| [tiff_directory.py](./tiff_directory.py) | `TiffDirectory`, the entries of one image file directory |
| [tiff_entry.py](./tiff_entry.py) | `TiffEntry`, one 12-byte directory entry as stored |
| [tiff_field_type.py](./tiff_field_type.py) | `TiffFieldType` enum of the field types written |
| [byte_order.py](./byte_order.py) | `ByteOrder` enum of the `MM` and `II` byte orders |

## Examples

```python
from datetime import datetime, timedelta, timezone

from geo_coordinate import Bearing, GeoCoordinate, NorthReference

from image_exif_extractor import ExifUpdate, ExifWriter

update = ExifUpdate(
    location=GeoCoordinate.from_degrees(35.681236, 139.767125),
    image_direction=Bearing.from_degrees(123.4, NorthReference.TRUE),
    captured_at=datetime(2024, 5, 1, 12, 34, 56, tzinfo=timezone(timedelta(hours=9))),
)
ExifWriter().write("photo.jpg", update, "photo_fixed.jpg")
```

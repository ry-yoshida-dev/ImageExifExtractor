# writing

## Overview

Lossless writing of Exif fields into JPEG files. `ExifWriter` sets the location, the direction
the camera faced and the time of capture of an `ExifUpdate`; fields left None are kept.

Only the Exif segment (APP1) of the file is replaced. Everything from the first scan on, the
compressed pixels and anything appended after them such as the second image of an MPO, and every
other segment are kept byte for byte, so the image is never re-encoded. In the Exif block, the
directories that change (GPS, Exif) are written anew at the end of the TIFF block, keeping their
other entries, and IFD0 is written anew pointing to them. Every value stored elsewhere keeps its
offset: the thumbnail directory (IFD1) and its image, the maker note, whose vendor formats hold
offsets of their own, and the values of the other tags. The replaced directories are left unused,
a few hundred bytes per edit. A JPEG without Exif gets a new block, and a missing GPS or Exif
directory is created.

| Field | Tags written | Also |
| --- | --- | --- |
| `location` | `GPSLatitude(Ref)`, `GPSLongitude(Ref)`, `GPSAltitude(Ref)` | `GPSVersionID` when absent; the altitude is removed when the location has none |
| `image_direction` | `GPSImgDirection`, `GPSImgDirectionRef` (`T` / `M`) | |
| `captured_at` | `DateTimeOriginal`, `OffsetTimeOriginal` when timezone-aware | `SubsecTimeOriginal` and a stale offset are removed |

Latitudes and longitudes are written to a ten-thousandth of an arcsecond, about 3 mm, and
directions and altitudes to a hundredth. XMP metadata, which some applications write besides
Exif, is not changed. Other formats, such as HEIF, are read but not written.

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

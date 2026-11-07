# ImageExifExtractor

## Overview

ImageExifExtractor (`image_exif_extractor`) is a Python package for extracting Exif metadata from image files.
`ExifExtractor` reads the Exif block from the file header, without decoding pixels, into an immutable `ExifMetadata` of typed `ExifEntry` items.
`ExifMetadata` also interprets the common fields: camera, capture settings, GPS location (as a [GeoCoordinate](https://github.com/ry-yoshida-dev/GeoCoordinate)), direction and orientation, and reads the height and gimbal angles DJI drones record in XMP.
`ExifWriter` writes the location, direction and time of capture back into JPEG files without re-encoding them.

## Installation

```bash
pip install .
```

To read HEIF / HEIC images (e.g. iPhone photos), install the `heif` extra:

```bash
pip install ".[heif]"
```

## Usage

```python
from PIL.ExifTags import Base

from image_exif_extractor import ExifExtractor, ExifIFD

metadata = ExifExtractor().extract("photo.jpg")

print(metadata.camera.model, metadata.capture_settings.captured_at)
print(metadata.find_value(ExifIFD.EXIF, Base.WhiteBalance))

coordinate = metadata.gps_coordinate
if coordinate is not None:
    print(coordinate.latitude.degree, coordinate.longitude.degree)

direction = metadata.image_direction
if direction is not None:
    print(direction.degree, direction.reference)

for entry in metadata.entries_in(ExifIFD.EXIF):
    print(entry.name, entry.value)
```

Extract many files lazily, restricted to some directories:

```python
import glob

extractor = ExifExtractor(ifds=[ExifIFD.BASE, ExifIFD.GPS])
for metadata in extractor.extract_all(sorted(glob.glob("photos/*.jpg"))):
    print(metadata.path, metadata.gps_coordinate)
```

Write a new location and direction into a JPEG file, keeping everything else byte for byte:

```python
from geo_coordinate import Bearing, GeoCoordinate, NorthReference

from image_exif_extractor import ExifUpdate, ExifWriter

update = ExifUpdate(
    location=GeoCoordinate.from_degrees(35.681236, 139.767125),
    image_direction=Bearing.from_degrees(123.4, NorthReference.TRUE),
)
ExifWriter().write("photo.jpg", update, "photo_fixed.jpg")
```

Print metadata as JSON, or export chosen tags of a directory to CSV (see `--help` for options):

```bash
python utils/print_exif_json.py photo.jpg --ifd gps
python utils/export_exif_csv.py image --tag Make --tag DateTimeOriginal --gps --output exif.csv
```

# ImageExifExtractor

## Overview

ImageExifExtractor (`image_exif_extractor`) is a Python package for extracting Exif metadata from image files.
`ExifExtractor` reads the Exif block from the file header, without decoding pixels, into an immutable `ExifMetadata` of typed `ExifEntry` items.
`ExifMetadata` also interprets the common fields: camera, capture settings, GPS location, direction and orientation.
The XMP metadata is kept as well, and `ExifMetadata.drone_attitude` reads the height and gimbal angles DJI drones record in it.

For package-level details, see [src/image_exif_extractor/README.md](src/image_exif_extractor/README.md).

## Installation

From the package root (the directory containing `pyproject.toml`):

```bash
pip install .
```

For development:

```bash
uv sync
```

To read HEIF / HEIC images (e.g. iPhone photos), install the `heif` extra:

```bash
pip install ".[heif]"
```

## Example

```python
from PIL.ExifTags import Base

from image_exif_extractor import ExifExtractor, ExifIFD

extractor = ExifExtractor()
metadata = extractor.extract("photo.jpg")

print(metadata.camera.model)
print(metadata.capture_settings.captured_at)
print(metadata.capture_settings.exposure_time)

coordinate = metadata.gps_coordinate
if coordinate is not None:
    print(coordinate.latitude.degree, coordinate.longitude.degree)
    if coordinate.altitude is not None:
        print(coordinate.altitude.meter)

direction = metadata.image_direction
if direction is not None:
    print(direction.degree, direction.reference)  # [123.4] NorthReference.TRUE

orientation = metadata.orientation
if orientation is not None:
    print(orientation.clockwise_rotation_degrees, orientation.is_mirrored)

print(metadata.find_value(ExifIFD.EXIF, Base.WhiteBalance))

for entry in metadata.entries_in(ExifIFD.EXIF):
    print(entry.name, entry.value)
```

Extract many files lazily, or restrict extraction to some directories:

```python
import glob

extractor = ExifExtractor(ifds=[ExifIFD.BASE, ExifIFD.GPS])
for metadata in extractor.extract_all(sorted(glob.glob("photos/*.jpg"))):
    print(metadata.path, metadata.gps_coordinate)
```

## GPS Location

`ExifMetadata.gps_coordinate` returns a single-element `GeoCoordinate` from
[GeoCoordinate](https://github.com/ry-yoshida-dev/GeoCoordinate), whose angles
and lengths are the unit-aware types of
[Units](https://github.com/ry-yoshida-dev/Units). Distances between photos
come from `GeoCoordinate.distance_to`:

```python
first = extractor.extract("first.jpg").gps_coordinate
second = extractor.extract("second.jpg").gps_coordinate
if first is not None and second is not None:
    print(first.distance_to(second).km)
```

## JSON Output

[utils/print_exif_json.py](utils/print_exif_json.py) prints the metadata of
each image as a JSON array.

```bash
python utils/print_exif_json.py photo1.jpg photo2.jpg
python utils/print_exif_json.py photo.jpg --ifd base --ifd gps --indent 0
python utils/print_exif_json.py photo.jpg --include-maker-note
```

A file that cannot be read is reported to stderr and skipped; the exit
status is then 1.

## CSV Export

[utils/export_exif_csv.py](utils/export_exif_csv.py) writes one CSV row per image in a
directory (`image` by default), with the chosen tags as columns. Tags are
given by name, without their directory, and matched case-insensitively.

```bash
python utils/export_exif_csv.py image --output exif.csv
python utils/export_exif_csv.py image --tag Make --tag FNumber --tag DateTimeOriginal --gps
python utils/export_exif_csv.py image --recursive
```

| Column | Content |
|--------|---------|
| `file` | Path relative to the scanned directory |
| One per `--tag` | Text as-is, numbers, sequences as a JSON array, empty when absent |
| `latitude`, `longitude`, `altitude` | With `--gps`: signed decimal degrees and meters |
| `error` | Why the file could not be read, empty otherwise |

The file is written as UTF-8 with BOM so spreadsheet applications detect the
encoding. An unreadable file keeps its row and makes the exit status 1.

## Development

```bash
uv run pytest
uv run ruff check .
uv run mypy
uv run basedpyright
```

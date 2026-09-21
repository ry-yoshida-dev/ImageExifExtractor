# utils

## Overview

Command line scripts built on the `image_exif_extractor` package. They are run from the repository root and are not part of the installed package.

## Components

| Component | Description |
|-----------|-------------|
| [print_exif_json.py](./print_exif_json.py) | `ExifJsonPrinter`, printing the metadata of images as a JSON array |
| [export_exif_csv.py](./export_exif_csv.py) | `ExifCsvExporter`, writing the selected tags of every image in a directory to one CSV file |

## Examples

```bash
python utils/print_exif_json.py photo.jpg --ifd gps
python utils/export_exif_csv.py image --output exif.csv
```

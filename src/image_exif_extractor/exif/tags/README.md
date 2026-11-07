# tags

## Overview

Representation of raw Exif tags: which directory a tag belongs to, its normalized value, and the JSON form of that value.

## Components

| Component | Description |
|-----------|-------------|
| [ifd.py](./ifd.py) | `ExifIFD` enum of directories (`BASE` / `EXIF` / `GPS` / `INTEROPERABILITY`) and their tag name tables |
| [entry.py](./entry.py) | `ExifEntry`, one tag id and its normalized value within a directory |
| [value.py](./value.py) | `ExifValue` and `JsonValue` type aliases |
| [normalizer.py](./normalizer.py) | `ExifValueNormalizer`, converting Pillow's raw values into `ExifValue` |
| [json_converter.py](./json_converter.py) | `ExifJsonConverter`, converting `ExifValue` into standard JSON values |

## Examples

```python
from image_exif_extractor.exif.tags import ExifEntry, ExifIFD, ExifJsonConverter

entry = ExifEntry(ifd=ExifIFD.EXIF, tag_id=0x9000, value=b"0232")
print(entry.name)
print(ExifJsonConverter.convert(entry.value))
```

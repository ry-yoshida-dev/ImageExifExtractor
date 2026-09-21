# exif

## Overview

`ExifMetadata`, the result `ExifExtractor.extract` returns, and the building blocks it is made of.
It is obtained from `ExifExtractor`; constructing it directly is intended for tests and synthetic data.

## Components

| Component | Description |
|-----------|-------------|
| [metadata.py](./metadata.py) | `ExifMetadata`, the extracted entries with typed lookups, interpreted fields and JSON export |
| [tags/](./tags/README.md) | Directories, entries and value normalization of raw Exif tags |
| [summaries/](./summaries/README.md) | Interpreted camera, capture settings and orientation |
| [gps/](./gps/README.md) | GPS tags read into a `GeoCoordinate`, and the Exif sea level reference |

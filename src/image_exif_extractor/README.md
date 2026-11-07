# image_exif_extractor

## Overview

Package for extracting the Exif tags of an image into immutable, typed entries, and interpreting the common fields. The location, direction and time of capture are written back into JPEG files losslessly by `ExifWriter`.

## Components

| Component | Description |
|-----------|-------------|
| [extractor.py](./extractor.py) | `ExifExtractor`, the entry point reading the selected directories of image files into `ExifMetadata` |
| [heif_support.py](./heif_support.py) | `HeifSupport`, registering the optional `pillow-heif` opener so HEIF / HEIC images can be read |
| [exif/](./exif/README.md) | `ExifMetadata` returned by `ExifExtractor`, with its raw tags and interpreted fields |
| [xmp/](./xmp/README.md) | `XmpPacket` of the XMP metadata, and the `DroneAttitude` of a drone's camera read from it |
| [writing/](./writing/README.md) | `ExifWriter` and `ExifUpdate`, which set the location, direction and time of capture of JPEG files without re-encoding them |
| [py.typed](./py.typed) | Marker declaring the package as typed for static analysers |

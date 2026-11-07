# summaries

## Overview

Interpretations of common Exif fields, each built through `from_metadata` from an `ExifMetadata`.

## Components

| Component | Description |
|-----------|-------------|
| [camera.py](./camera.py) | `CameraInfo`, camera and lens make, model, serial number and software |
| [capture_settings.py](./capture_settings.py) | `CaptureSettings`, exposure time, f-number, ISO, focal length and capture time |
| [datetime_parser.py](./datetime_parser.py) | `ExifDateTimeParser`, combining the date-time, offset and sub-second tags into a `datetime` |
| [orientation.py](./orientation.py) | `Orientation` enum of the eight Exif orientations, with rotation and mirroring |

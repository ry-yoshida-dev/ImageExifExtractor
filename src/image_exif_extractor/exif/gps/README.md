# gps

## Overview

Interpretation of the GPS directory into a [`GeoCoordinate`](https://github.com/ry-yoshida-dev/GeoCoordinate), holding signed `units.Angle` latitude and longitude and an optional signed `Altitude`, and of its directions into a `geo_coordinate.Bearing` from true or magnetic north.

## Components

| Component | Description |
|-----------|-------------|
| [reader.py](./reader.py) | `GpsCoordinateReader`, whose `from_metadata` combines the GPS tags of an `ExifMetadata` into a single `GeoCoordinate` |
| [bearing_reader.py](./bearing_reader.py) | `GpsBearingReader`, which reads one direction of an `ExifMetadata` into a `Bearing` |
| [gps_bearing_kind.py](./gps_bearing_kind.py) | `GpsBearingKind` enum of the directions recorded: faced (`GPSImgDirection`), moved in (`GPSTrack`) and to the destination (`GPSDestBearing`), with their reference tags |
| [altitude_reference.py](./altitude_reference.py) | `AltitudeReference` enum (`ABOVE_SEA_LEVEL` / `BELOW_SEA_LEVEL`) of `GPSAltitudeRef` |

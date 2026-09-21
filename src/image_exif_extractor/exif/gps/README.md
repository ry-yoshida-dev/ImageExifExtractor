# gps

## Overview

Interpretation of the GPS directory into a [`GeoCoordinate`](https://github.com/ry-yoshida-dev/GeoCoordinate), holding signed `units.Angle` latitude and longitude and an optional signed `Altitude`.

## Components

| Component | Description |
|-----------|-------------|
| [reader.py](./reader.py) | `GpsCoordinateReader`, whose `from_metadata` combines the GPS tags of an `ExifMetadata` into a single `GeoCoordinate` |
| [altitude_reference.py](./altitude_reference.py) | `AltitudeReference` enum (`ABOVE_SEA_LEVEL` / `BELOW_SEA_LEVEL`) of `GPSAltitudeRef` |

## Absent and Undefined Values

`ExifMetadata.gps_coordinate` is `None` when latitude or longitude is absent,
or undefined as a rational with a zero denominator. A coordinate present
without its hemisphere reference raises `ValueError`. `altitude` is `None`
when unrecorded or undefined, and a missing `GPSAltitudeRef` means above sea level, as the
Exif specification defines.

## Sexagesimal Components

Each angle is read into a `units.DegreesMinutesSeconds` through
`DegreesMinutesSeconds.normalized`, with `GPSLatitudeRef` / `GPSLongitudeRef`
parsed by `geo_coordinate.LatitudeHemisphere` / `LongitudeHemisphere` as
`is_negative`. Writers that store non-canonical components, such as
fractional minutes with zero seconds, are therefore carried into canonical
form, while a negative component raises `ValueError`.

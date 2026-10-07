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

## Directions

`ExifMetadata.image_direction` reads `GPSImgDirection` with `GPSImgDirectionRef`, and
`ExifMetadata.gps_bearing` any `GpsBearingKind`. The reference `T` gives
`NorthReference.TRUE` and `M` `NorthReference.MAGNETIC`; a direction without its reference
is taken as measured from true north, since the specification gives no default, and any other
letter raises `ValueError`. A recorded 360 is read as 0, and an absent or undefined direction
as None.

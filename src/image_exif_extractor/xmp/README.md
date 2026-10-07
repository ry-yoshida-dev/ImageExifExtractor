# xmp

## Overview

XMP metadata of images, which vendors use for what Exif has no tag for. `ExifExtractor` keeps
the XMP packet Pillow (or pillow-heif) reads from the file header as `ExifMetadata.xmp`, and
`ExifMetadata.drone_attitude` reads from it how a drone held its camera.

`XmpPacket` looks up simple properties by qualified name, whether written as an attribute of an
`rdf:Description` (`drone-dji:GimbalYawDegree="-87.30"`) or as an element of their own. The
packet is matched as text rather than parsed as XML, so a truncated or vendor-mangled packet
still yields the properties it holds.

`DroneAttitudeReader` reads the properties DJI defines, which other makers follow:

| Property | `DroneAttitude` field | Read as |
| --- | --- | --- |
| `drone-dji:RelativeAltitude` | `relative_altitude` | Signed `Altitude` in meters above the take-off point |
| `drone-dji:GimbalYawDegree` | `gimbal_yaw` | `Bearing` from true north, wrapped into [0, 360) |
| `drone-dji:GimbalPitchDegree` | `gimbal_pitch` | `Angle`, -90 degrees straight down |
| `drone-dji:GimbalRollDegree` | `gimbal_roll` | `Angle`, or None |
| `drone-dji:FlightYawDegree` | `flight_yaw` | `Bearing` from true north, or None |

A photo without the altitude, the gimbal yaw or the gimbal pitch has no attitude.

## Components

| Component | Description |
|-----------|-------------|
| [xmp_packet.py](./xmp_packet.py) | `XmpPacket`, the text of an XMP packet and lookups of its simple properties |
| [drone_attitude_reader.py](./drone_attitude_reader.py) | `DroneAttitudeReader`, which reads the DJI properties into a `DroneAttitude` |
| [drone_attitude.py](./drone_attitude.py) | `DroneAttitude`, the height and gimbal angles of a drone's camera |

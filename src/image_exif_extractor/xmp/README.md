# xmp

## Overview

XMP metadata of images, which vendors use for what Exif has no tag for. `ExifExtractor` keeps the packet as
`ExifMetadata.xmp`, and `ExifMetadata.drone_attitude` reads from it how a DJI drone held its camera.

## Components

| Component | Description |
|-----------|-------------|
| [xmp_packet.py](./xmp_packet.py) | `XmpPacket`, the text of an XMP packet and lookups of its simple properties |
| [drone_attitude_reader.py](./drone_attitude_reader.py) | `DroneAttitudeReader`, which reads the DJI properties into a `DroneAttitude` |
| [drone_attitude.py](./drone_attitude.py) | `DroneAttitude`, the height and gimbal angles of a drone's camera |

"""XMP metadata of images, such as the attitude of a drone's camera."""

from .drone_attitude import DroneAttitude
from .drone_attitude_reader import DroneAttitudeReader
from .xmp_packet import XmpPacket

__all__ = ["DroneAttitude", "DroneAttitudeReader", "XmpPacket"]

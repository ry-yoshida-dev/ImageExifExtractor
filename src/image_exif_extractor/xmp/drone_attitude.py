from __future__ import annotations

from dataclasses import dataclass

from geo_coordinate import Altitude, Bearing
from units import Angle


@dataclass(frozen=True)
class DroneAttitude:
    """
    How a drone held its camera when it took a photo, as its XMP records.

    Attributes
    ----------
    relative_altitude : Altitude
        The height above the place the drone took off from, which over flat ground
        is the height above the ground photographed.
    gimbal_yaw : Bearing
        The direction the top of the camera's sensor faced, from true north.
    gimbal_pitch : Angle
        The tilt of the camera, 0 at the horizon and -90 degrees straight down.
    gimbal_roll : Angle | None
        The roll of the camera, or None when not recorded.
    flight_yaw : Bearing | None
        The heading of the aircraft, from true north, or None when not recorded.
    """

    relative_altitude: Altitude
    gimbal_yaw: Bearing
    gimbal_pitch: Angle
    gimbal_roll: Angle | None
    flight_yaw: Bearing | None

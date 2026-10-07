from __future__ import annotations

from typing import Final

import numpy as np
from geo_coordinate import Altitude, Bearing
from units import Angle, AngleUnit, LengthUnit

from .drone_attitude import DroneAttitude
from .xmp_packet import XmpPacket

RELATIVE_ALTITUDE: Final[str] = "drone-dji:RelativeAltitude"
GIMBAL_YAW: Final[str] = "drone-dji:GimbalYawDegree"
GIMBAL_PITCH: Final[str] = "drone-dji:GimbalPitchDegree"
GIMBAL_ROLL: Final[str] = "drone-dji:GimbalRollDegree"
FLIGHT_YAW: Final[str] = "drone-dji:FlightYawDegree"


class DroneAttitudeReader:
    """
    Read the attitude of a drone's camera from the XMP properties DJI defines.

    DJI aircraft, and others following them, record `drone-dji:RelativeAltitude`
    in meters and the gimbal and flight angles in degrees, yaws clockwise from true
    north within [-180, 180]. Yaws are turned into bearings within [0, 360).
    """

    @staticmethod
    def from_packet(packet: XmpPacket) -> DroneAttitude | None:
        """
        Read the attitude.

        Parameters
        ----------
        packet : XmpPacket
            The XMP of the photo.

        Returns
        -------
        DroneAttitude | None
            The attitude, or None when the relative altitude, the gimbal yaw or the
            gimbal pitch is not recorded.

        Raises
        ------
        ValueError
            If a property is present but not a finite number.
        """
        altitude = packet.find_number(RELATIVE_ALTITUDE)
        yaw = packet.find_number(GIMBAL_YAW)
        pitch = packet.find_number(GIMBAL_PITCH)
        if altitude is None or yaw is None or pitch is None:
            return None
        roll = packet.find_number(GIMBAL_ROLL)
        flight_yaw = packet.find_number(FLIGHT_YAW)
        return DroneAttitude(
            relative_altitude=Altitude(value=np.array([altitude]), unit=LengthUnit.M),
            gimbal_yaw=Bearing.from_degrees(yaw),
            gimbal_pitch=Angle(value=np.array([pitch]), unit=AngleUnit.DEGREE),
            gimbal_roll=None
            if roll is None
            else Angle(value=np.array([roll]), unit=AngleUnit.DEGREE),
            flight_yaw=None if flight_yaw is None else Bearing.from_degrees(flight_yaw),
        )

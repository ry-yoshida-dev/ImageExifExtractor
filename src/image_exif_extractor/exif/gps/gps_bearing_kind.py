from __future__ import annotations

from enum import Enum

from PIL.ExifTags import GPS


class GpsBearingKind(Enum):
    """
    The directions the GPS directory records, each as a value and a north reference.

    Attributes
    ----------
    IMAGE_DIRECTION
        The direction the camera faced, `GPSImgDirection` and `GPSImgDirectionRef`.
    TRACK
        The direction the camera moved in, `GPSTrack` and `GPSTrackRef`.
    DESTINATION_BEARING
        The bearing to the destination, `GPSDestBearing` and `GPSDestBearingRef`.
    """

    IMAGE_DIRECTION = "image_direction"
    TRACK = "track"
    DESTINATION_BEARING = "destination_bearing"

    @property
    def value_tag_id(self) -> int:
        """
        Return the tag holding the direction in degrees.

        Returns
        -------
        int
            The GPS tag id.
        """
        match self:
            case GpsBearingKind.IMAGE_DIRECTION:
                return int(GPS.GPSImgDirection)
            case GpsBearingKind.TRACK:
                return int(GPS.GPSTrack)
            case GpsBearingKind.DESTINATION_BEARING:
                return int(GPS.GPSDestBearing)

    @property
    def reference_tag_id(self) -> int:
        """
        Return the tag holding the north the direction is measured from.

        Returns
        -------
        int
            The GPS tag id, whose value is `T` or `M`.
        """
        match self:
            case GpsBearingKind.IMAGE_DIRECTION:
                return int(GPS.GPSImgDirectionRef)
            case GpsBearingKind.TRACK:
                return int(GPS.GPSTrackRef)
            case GpsBearingKind.DESTINATION_BEARING:
                return int(GPS.GPSDestBearingRef)

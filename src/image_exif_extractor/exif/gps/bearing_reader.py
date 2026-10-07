from __future__ import annotations

from typing import TYPE_CHECKING

from geo_coordinate import Bearing, NorthReference

from ..tags import ExifIFD
from .gps_bearing_kind import GpsBearingKind

if TYPE_CHECKING:
    from ..metadata import ExifMetadata


class GpsBearingReader:
    """
    Read a direction of the GPS directory into a `Bearing`.

    Exif stores a direction as unsigned degrees with a separate `T` (true north) or
    `M` (magnetic north) reference. A direction recorded without its reference is
    taken as measured from true north, since the specification gives no default
    and true north is what most writers record.
    """

    @staticmethod
    def from_metadata(metadata: ExifMetadata, kind: GpsBearingKind) -> Bearing | None:
        """
        Read one direction.

        Parameters
        ----------
        metadata : ExifMetadata
            The metadata to read.
        kind : GpsBearingKind
            Which direction to read.

        Returns
        -------
        Bearing | None
            A single bearing within [0, 360) degrees, a recorded 360 read as 0, or
            None when the direction is absent or undefined (a rational with a zero
            denominator).

        Raises
        ------
        ValueError
            If the reference is neither `T` nor `M`.
        TypeError
            If a tag holds a value of an unexpected type.
        """
        degree = metadata.find_number(ExifIFD.GPS, kind.value_tag_id)
        if degree is None:
            return None
        reference_text = metadata.find_text(ExifIFD.GPS, kind.reference_tag_id)
        reference = (
            NorthReference.TRUE if reference_text is None else NorthReference(reference_text)
        )
        return Bearing.from_degrees(degree, reference)

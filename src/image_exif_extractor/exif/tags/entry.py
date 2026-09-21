from dataclasses import dataclass

from .ifd import ExifIFD
from .value import ExifValue


@dataclass(frozen=True)
class ExifEntry:
    """
    One Exif tag and its normalized value.

    Attributes
    ----------
    ifd : ExifIFD
        The directory the tag is stored in.
    tag_id : int
        The numeric tag id.
    value : ExifValue
        The normalized value of the tag.
    """

    ifd: ExifIFD
    tag_id: int
    value: ExifValue

    @property
    def name(self) -> str:
        """
        Human-readable name of the tag.

        Returns
        -------
        str
            The registered tag name, or `Unknown0x....` for an unregistered id.
        """
        return self.ifd.resolve_tag_name(self.tag_id)

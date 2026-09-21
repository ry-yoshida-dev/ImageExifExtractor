from collections.abc import Mapping
from enum import Enum

from PIL import ExifTags


class ExifIFD(Enum):
    """
    Image File Directory (IFD) an Exif tag is stored in.

    Attributes
    ----------
    BASE
        The primary image directory (IFD0), holding camera make, model and orientation.
    EXIF
        The Exif sub-directory, holding capture settings such as exposure and ISO.
    GPS
        The GPS sub-directory, holding the location the image was captured at.
    INTEROPERABILITY
        The interoperability sub-directory, nested inside the Exif sub-directory.
    """

    BASE = "base"
    EXIF = "exif"
    GPS = "gps"
    INTEROPERABILITY = "interoperability"

    @property
    def pointer_tag_id(self) -> int | None:
        """
        Tag id whose value is the offset of this directory inside its parent.

        Returns
        -------
        int | None
            The pointer tag id, or None for `BASE`, which is not nested.
        """
        match self:
            case ExifIFD.BASE:
                return None
            case ExifIFD.EXIF:
                return int(ExifTags.IFD.Exif)
            case ExifIFD.GPS:
                return int(ExifTags.IFD.GPSInfo)
            case ExifIFD.INTEROPERABILITY:
                return int(ExifTags.IFD.Interop)

    @property
    def tag_names(self) -> Mapping[int, str]:
        """
        Table of the tag names defined for this directory.

        Returns
        -------
        Mapping[int, str]
            Tag names keyed by tag id.
        """
        match self:
            case ExifIFD.GPS:
                return ExifTags.GPSTAGS
            case ExifIFD.BASE | ExifIFD.EXIF | ExifIFD.INTEROPERABILITY:
                return ExifTags.TAGS

    def resolve_tag_name(self, tag_id: int) -> str:
        """
        Resolve a tag id to its name within this directory.

        Parameters
        ----------
        tag_id : int
            The tag id to resolve.

        Returns
        -------
        str
            The registered tag name, or `Unknown0x....` for an unregistered id.
        """
        return self.tag_names.get(tag_id, f"Unknown0x{tag_id:04X}")

    @classmethod
    def pointer_tag_ids(cls) -> frozenset[int]:
        """
        Collect the tag ids that only point at a nested directory.

        Returns
        -------
        frozenset[int]
            Pointer tag ids, which carry offsets rather than metadata.
        """
        return frozenset(
            pointer_tag_id for ifd in cls if (pointer_tag_id := ifd.pointer_tag_id) is not None
        )

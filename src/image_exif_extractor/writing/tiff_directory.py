from __future__ import annotations

from dataclasses import dataclass

from .tiff_entry import TiffEntry


@dataclass(frozen=True)
class TiffDirectory:
    """
    The entries of one image file directory and the offset of the next.

    Attributes
    ----------
    entries
        The entries, sorted by tag as TIFF requires.
    next_offset
        The offset of the next directory, such as IFD1 holding the thumbnail after
        IFD0, or 0 when none follows.

    Raises
    ------
    ValueError
        If the entries are not sorted by tag or a tag repeats.
    """

    entries: tuple[TiffEntry, ...]
    next_offset: int = 0

    def __post_init__(self) -> None:
        tags = [entry.tag for entry in self.entries]
        if tags != sorted(set(tags)):
            raise ValueError("Directory entries must be sorted by tag without repeats")

    def find(self, tag: int) -> TiffEntry | None:
        """
        Look up the entry of a tag.

        Parameters
        ----------
        tag : int
            The tag id.

        Returns
        -------
        TiffEntry | None
            The entry, or None when the tag is absent.
        """
        return next((entry for entry in self.entries if entry.tag == tag), None)

    def with_entry(self, entry: TiffEntry) -> TiffDirectory:
        """
        Set the entry of a tag, replacing any entry of the same tag.

        Parameters
        ----------
        entry : TiffEntry
            The entry to set.

        Returns
        -------
        TiffDirectory
            A directory holding the entry in tag order.
        """
        others = [existing for existing in self.entries if existing.tag != entry.tag]
        return TiffDirectory(
            entries=tuple(sorted([*others, entry], key=lambda candidate: candidate.tag)),
            next_offset=self.next_offset,
        )

    def without(self, *tags: int) -> TiffDirectory:
        """
        Remove the entries of some tags.

        Parameters
        ----------
        *tags : int
            The tag ids; absent ones are ignored.

        Returns
        -------
        TiffDirectory
            A directory without those tags.
        """
        removed = set(tags)
        return TiffDirectory(
            entries=tuple(entry for entry in self.entries if entry.tag not in removed),
            next_offset=self.next_offset,
        )

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Final

QUALIFIED_NAME_PATTERN: Final[str] = r"[A-Za-z_][\w.-]*:[A-Za-z_][\w.-]*"


@dataclass(frozen=True)
class XmpPacket:
    """
    The XMP metadata of an image, as the text of its packet.

    XMP is RDF written as XML, where a simple property is either an attribute of an
    `rdf:Description` or an element of its own. Vendors such as DJI record what Exif
    has no tag for, like the attitude of a drone's gimbal, as such properties, so
    they are looked up by their qualified name in either form.

    Attributes
    ----------
    text
        The packet, from `<?xpacket begin` or `<x:xmpmeta` on.
    """

    text: str

    @classmethod
    def from_bytes(cls, data: bytes) -> XmpPacket:
        """
        Decode a packet, as Pillow and pillow-heif keep it in `Image.info["xmp"]`.

        Parameters
        ----------
        data : bytes
            The packet, in UTF-8 as XMP requires; invalid bytes are replaced.

        Returns
        -------
        XmpPacket
            The packet.
        """
        return cls(text=data.decode("utf-8", errors="replace"))

    def find_text(self, qualified_name: str) -> str | None:
        """
        Look up a simple property by its qualified name.

        Parameters
        ----------
        qualified_name : str
            The prefix and local name, such as `drone-dji:RelativeAltitude`.

        Returns
        -------
        str | None
            The value without surrounding whitespace, or None when the property is
            absent or empty.

        Raises
        ------
        ValueError
            If `qualified_name` is not a prefix and a local name joined by a colon.
        """
        if re.fullmatch(QUALIFIED_NAME_PATTERN, qualified_name) is None:
            raise ValueError(f"Invalid qualified name: {qualified_name!r}")
        escaped = re.escape(qualified_name)
        attribute = re.search(rf"\s{escaped}\s*=\s*([\"'])(.*?)\1", self.text, re.DOTALL)
        element = re.search(rf"<{escaped}(?:\s[^>]*)?>([^<]*)</{escaped}>", self.text)
        match_value = (
            attribute.group(2)
            if attribute is not None
            else element.group(1)
            if element is not None
            else None
        )
        if match_value is None:
            return None
        return match_value.strip() or None

    def find_number(self, qualified_name: str) -> float | None:
        """
        Look up a numeric property by its qualified name.

        Parameters
        ----------
        qualified_name : str
            The prefix and local name, such as `drone-dji:GimbalPitchDegree`.

        Returns
        -------
        float | None
            The number, with an explicit `+` sign allowed, or None when the property
            is absent.

        Raises
        ------
        ValueError
            If the property is present but not a finite number.
        """
        text = self.find_text(qualified_name)
        if text is None:
            return None
        try:
            number = float(text)
        except ValueError as error:
            raise ValueError(f"{qualified_name} is not a number: {text!r}") from error
        if not math.isfinite(number):
            raise ValueError(f"{qualified_name} is not finite: {text!r}")
        return number

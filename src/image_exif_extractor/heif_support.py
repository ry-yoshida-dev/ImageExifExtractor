from importlib.util import find_spec
from typing import ClassVar


class HeifSupport:
    """
    Optional HEIF / HEIC support through the `pillow-heif` plugin.

    Pillow cannot open HEIF images on its own. When the `heif` extra is
    installed, registering the plugin lets `PIL.Image.open` read them.
    """

    PLUGIN_PACKAGE: ClassVar[str] = "pillow_heif"

    @staticmethod
    def is_available() -> bool:
        """
        Whether the `pillow-heif` plugin is installed.

        Returns
        -------
        bool
            True when `pillow_heif` can be imported.
        """
        return find_spec(HeifSupport.PLUGIN_PACKAGE) is not None

    @staticmethod
    def register() -> None:
        """
        Register the HEIF opener with Pillow.

        Calling this repeatedly is harmless, since registration overwrites the
        previous entry.

        Raises
        ------
        ModuleNotFoundError
            If the `pillow-heif` plugin is not installed.
        """
        if not HeifSupport.is_available():
            raise ModuleNotFoundError(
                f"{HeifSupport.PLUGIN_PACKAGE} is not installed; install the heif extra"
            )

        from pillow_heif.as_plugin import (
            register_heif_opener,  # pyright: ignore[reportUnknownVariableType]
        )

        register_heif_opener()

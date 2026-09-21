import pytest
from PIL import Image

from image_exif_extractor import HeifSupport


class TestHeifSupport:
    def test_registers_heif_opener_when_installed(self) -> None:
        assert HeifSupport.is_available()
        HeifSupport.register()
        assert ".heic" in Image.registered_extensions()

    def test_register_raises_when_plugin_is_absent(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(HeifSupport, "PLUGIN_PACKAGE", "absent_heif_plugin")
        assert not HeifSupport.is_available()
        with pytest.raises(ModuleNotFoundError, match="absent_heif_plugin"):
            HeifSupport.register()

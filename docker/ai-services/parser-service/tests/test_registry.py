import pytest

from app.adapters.base import ParserAdapter, UnsupportedFileTypeError
from app.registry import ParserRegistry, default_registry


class _FakeAdapter(ParserAdapter):
    def __init__(self, extensions):
        self._extensions = extensions

    @property
    def supported_extensions(self):
        return self._extensions

    def parse(self, content, filename):
        raise NotImplementedError


class TestParserRegistry:
    def test_register_va_resolve_theo_extension(self):
        registry = ParserRegistry()
        adapter = _FakeAdapter(["foo"])
        registry.register(adapter)

        assert registry.resolve("file.foo") is adapter
        assert registry.resolve("FILE.FOO") is adapter  # không phân biệt hoa/thường

    def test_resolve_khong_co_adapter_nem_unsupported(self):
        registry = ParserRegistry()
        with pytest.raises(UnsupportedFileTypeError):
            registry.resolve("file.unknown")

    def test_resolve_khong_co_duoi_file_nem_unsupported(self):
        registry = ParserRegistry()
        with pytest.raises(UnsupportedFileTypeError):
            registry.resolve("khongduoifile")

    def test_dang_ky_trung_extension_nem_valueerror(self):
        registry = ParserRegistry()
        registry.register(_FakeAdapter(["foo"]))
        with pytest.raises(ValueError, match="đã được đăng ký"):
            registry.register(_FakeAdapter(["foo"]))

    def test_default_registry_ho_tro_du_cac_dinh_dang_sprint_1_1_va_1_1b(self):
        registry = default_registry()
        supported = registry.supported_extensions()
        for ext in ["docx", "xlsx", "pptx", "pdf", "png", "txt", "md", "html", "dxf", "dwg", "vsdx", "drawio"]:
            assert ext in supported, f"Thiếu hỗ trợ .{ext}"

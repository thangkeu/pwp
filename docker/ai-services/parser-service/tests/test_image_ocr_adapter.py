import pytesseract

from app.adapters.base import DependencyUnavailableError, ParsingError
from app.adapters.image_ocr_adapter import ImageOcrAdapter


class TestImageOcrAdapter:
    def test_supported_extensions(self):
        assert set(ImageOcrAdapter().supported_extensions) == {"png", "jpg", "jpeg", "tiff", "bmp"}

    def test_parse_ocr_ra_text(self, sample_png_bytes):
        result = ImageOcrAdapter().parse(sample_png_bytes, "scan.png")

        # OCR trên ảnh test đơn giản (không noise) — kỳ vọng nhận diện được ít nhất 1 phần chữ.
        assert "OCR" in result.text.upper() or "TEST" in result.text.upper()
        assert len(result.images) == 1
        assert result.images[0].width == 300
        assert result.images[0].height == 80
        assert result.images[0].content_base64 is not None

    def test_parse_file_hong_nem_parsing_error(self):
        try:
            ImageOcrAdapter().parse(b"not an image", "fake.png")
            assert False, "Phải ném ParsingError"
        except ParsingError:
            pass

    def test_ocr_languages_cau_hinh_duoc_khong_hardcode(self):
        adapter = ImageOcrAdapter(ocr_languages="eng")
        assert adapter._ocr_languages == "eng"

    def test_tesseract_cmd_cau_hinh_duoc_cho_windows(self):
        """
        Trên Windows, tesseract.exe thường không tự có trong PATH — adapter phải cho phép
        trỏ thẳng đường dẫn qua constructor (tương ứng biến môi trường PARSER_TESSERACT_CMD).
        """
        original = pytesseract.pytesseract.tesseract_cmd
        try:
            ImageOcrAdapter(tesseract_cmd=r"C:\Program Files\Tesseract-OCR\tesseract.exe")
            assert pytesseract.pytesseract.tesseract_cmd == r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        finally:
            pytesseract.pytesseract.tesseract_cmd = original  # không rò rỉ side-effect sang test khác

    def test_khong_tim_thay_tesseract_nem_dependency_unavailable_error(self, sample_png_bytes, monkeypatch):
        """
        Mô phỏng đúng lỗi thực tế người dùng gặp trên Windows khi chưa cài Tesseract OCR:
        adapter phải ném DependencyUnavailableError (rõ ràng, có hướng dẫn khắc phục) thay vì
        để traceback thô của pytesseract lộ ra ngoài.
        """

        def _raise_not_found(*args, **kwargs):  # noqa: ARG001
            raise pytesseract.TesseractNotFoundError()

        monkeypatch.setattr(pytesseract, "image_to_string", _raise_not_found)

        try:
            ImageOcrAdapter().parse(sample_png_bytes, "scan.png")
            assert False, "Phải ném DependencyUnavailableError"
        except DependencyUnavailableError as exc:
            assert "PARSER_TESSERACT_CMD" in str(exc)

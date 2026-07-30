from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_tra_ok(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


class TestParsersEndpoint:
    def test_list_parsers_tra_danh_sach_extension(self):
        res = client.get("/parsers")
        assert res.status_code == 200
        assert "docx" in res.json()["supported_extensions"]


class TestParseEndpoint:
    def test_parse_docx_thanh_cong(self, sample_docx_bytes):
        docx_mime = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        res = client.post(
            "/parse",
            files={"file": ("baogia.docx", sample_docx_bytes, docx_mime)},
        )
        assert res.status_code == 200
        body = res.json()
        assert "Báo giá Fortigate 100F" in body["text"]
        assert body["metadata"]["parser_name"] == "DocxAdapter"

    def test_parse_dinh_dang_khong_ho_tro_tra_415(self):
        res = client.post(
            "/parse",
            files={"file": ("mohinh.rvt", b"fake revit content", "application/octet-stream")},
        )
        assert res.status_code == 415
        assert "rvt" in res.json()["detail"]

    def test_parse_file_hong_tra_422(self):
        res = client.post(
            "/parse",
            files={"file": ("baogia.docx", b"not a real docx", "application/octet-stream")},
        )
        assert res.status_code == 422

    def test_parse_dwg_tra_503_voi_huong_dan_convert(self):
        res = client.post(
            "/parse",
            files={"file": ("sodo.dwg", b"fake dwg binary content", "application/octet-stream")},
        )
        assert res.status_code == 503
        assert "DXF" in res.json()["detail"]

    def test_parse_thieu_tesseract_tra_503(self, sample_png_bytes, monkeypatch):
        import pytesseract

        def _raise_not_found(*args, **kwargs):  # noqa: ARG001
            raise pytesseract.TesseractNotFoundError()

        monkeypatch.setattr(pytesseract, "image_to_string", _raise_not_found)

        res = client.post("/parse", files={"file": ("scan.png", sample_png_bytes, "image/png")})
        assert res.status_code == 503
        assert "PARSER_TESSERACT_CMD" in res.json()["detail"]

    def test_parse_vuot_gioi_han_dung_luong_tra_413(self, monkeypatch):
        from dataclasses import replace

        from app import main as main_module

        # settings là frozen dataclass (immutable) — thay cả object thay vì sửa field,
        # đúng tinh thần immutable config, tránh side-effect giữa các test khác.
        monkeypatch.setattr(main_module, "settings", replace(main_module.settings, max_upload_mb=0))
        res = client.post(
            "/parse",
            files={"file": ("note.txt", b"some content", "text/plain")},
        )
        assert res.status_code == 413

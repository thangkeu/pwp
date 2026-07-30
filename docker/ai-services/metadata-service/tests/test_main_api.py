from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_tra_ok(self):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"


class TestExtractEndpoint:
    def test_extract_thanh_cong(self):
        res = client.post(
            "/metadata/extract",
            json={"text": "Sử dụng FortiGate 100F cho chi nhánh, ngày 12/07/2026.", "filename": "test.docx"},
        )
        assert res.status_code == 200
        body = res.json()
        assert any(m["vendor"] == "Fortinet" for m in body["vendor_models"])
        assert "12/07/2026" in body["dates_found"]

    def test_extract_khong_can_filename(self):
        res = client.post("/metadata/extract", json={"text": "Văn bản không có filename."})
        assert res.status_code == 200

    def test_extract_thieu_text_tra_422_validation_error(self):
        res = client.post("/metadata/extract", json={"filename": "test.docx"})
        assert res.status_code == 422

    def test_extract_vuot_gioi_han_dung_luong_tra_413(self, monkeypatch):
        from dataclasses import replace

        from app import main as main_module

        monkeypatch.setattr(main_module, "settings", replace(main_module.settings, max_text_length_mb=0))
        res = client.post("/metadata/extract", json={"text": "noi dung bat ky"})
        assert res.status_code == 413

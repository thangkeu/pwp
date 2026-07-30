# Changelog

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/), quy ước version theo
[Master Plan Mục 9](docs adr — release strategy): MAJOR.MINOR.PATCH cho mỗi service Docker.

## [gateway 0.4.0] + [metadata-service 0.1.0] — Sprint 1.2 — 2026-07-29

### Added
- `scripts/windows/stop-all-windows.ps1` — dừng toàn bộ Docker Compose + tiến trình giữ cổng
  8001/8002/3000 trước khi khởi động lại, để tránh lỗi "service cũ giữ cổng" đã gặp ở Sprint 1.1b.
- **Gateway**: `domain/DocumentItem.js`, `repositories/documentRepository.js`
  (`InMemoryDocumentRepository`), `services/syncEngine.js` (2 chế độ `full`/`delta`),
  `connectors/googleDriveConnector.js`, `connectors/microsoftGraphConnector.js` — 30 test mới
  (tổng Gateway: 64 test).
- **Metadata Service mới** (`docker/ai-services/metadata-service/`, Python/FastAPI):
  `VendorModelExtractor`, `DateExtractor`, `VersionExtractor`, `SecurityLevelClassifier`,
  `DocumentTypeClassifier`, `DictionaryExtractor` (Customer/Project/Industry), orchestrator
  `MetadataEngine`, endpoint `POST /metadata/extract` — 44 test.
- `docker-compose.yml`: thêm service `metadata-service` (port 8002).
- CI/CD: `lint-and-test-metadata-service` + `build-image-metadata-service`.

### Known gaps (chuyển sang Sprint sau)
- Dictionary Customer/Project mặc định RỖNG — cần công ty cung cấp danh sách thật.
- `GoogleDriveConnector.path` chưa resolve theo cây folder cha (`parents`).
- Chưa nối tự động Parser Service → Metadata Engine → Postgres qua Event Bus (2 service hiện độc lập).
- `PostgresDocumentRepository` thật chưa viết — `InMemoryDocumentRepository` chỉ dùng cho test/demo.
- 2 connector Delta chưa test với API Google/Microsoft thật (chỉ test với `fetchImpl` giả lập).

## [parser-service 0.2.0] — Sprint 1.1b — 2026-07-28

### Added
- `app/adapters/cad_adapter.py` — `CadAdapter`: `.dxf` hỗ trợ thật qua `ezdxf` (TEXT/MTEXT/ATTRIB
  + block name + layer); `.dwg` trả `DependencyUnavailableError` (503) kèm hướng dẫn convert
  sang DXF cụ thể (ODA File Converter hoặc AutoCAD/LibreCAD/QCAD "Save As").
- `app/adapters/visio_adapter.py` — `VisioAdapter`: `.vsdx` qua thư viện `vsdx`, trích text mọi
  shape theo từng page; dùng file tạm (thư viện chỉ nhận path thật) + dọn dẹp trong `finally`.
- `app/adapters/drawio_adapter.py` — `DrawioAdapter`: `.drawio`, tự phát hiện và xử lý cả 2 dạng
  lưu của app.diagrams.net (XML thô và XML nén base64+deflate+urlencode).
- `requirements.txt`: thêm `ezdxf==1.4.4`, `vsdx==0.6.1` (thuần Python, không cần binary hệ điều hành).
- 17 test case mới (CAD 4, Visio 4, Draw.io 4, sửa Registry + API 5) — tổng 49 test (từ 32).
- `README_SPRINT1.1b.md` — bàn giao đầy đủ 17 mục.

### Changed
- `test_main_api.py::test_parse_dinh_dang_khong_ho_tro_tra_415`: đổi ví dụ từ `.dwg` sang `.rvt`
  vì `.dwg` giờ có adapter đăng ký (trả 503, không còn 415).
- `README_SPRINT1.1.md` Mục 2: đánh dấu CAD/Visio/Draw.io đã hoàn thành (dẫn sang README này).

### Known gaps (ngoài phạm vi Sprint 1.1b, ghi nhận để cân nhắc sau)
- DXF/Visio mới trích **text**, chưa trích **hình học** (đường/vòng tròn/toạ độ) để dựng lại bản vẽ.
- `.dwg` chưa parse trực tiếp được (cần tích hợp ODA File Converter dạng CLI nếu nhu cầu cao).
- `.vsd` (Visio nhị phân cũ, trước 2013) chưa hỗ trợ — chỉ `.vsdx` (OOXML).
- Chưa test với file DXF/VSDX/Draw.io **thật** của dự án (mới test bằng fixture tự sinh qua `ezdxf`/`vsdx`).

## [parser-service 0.1.1] — Sprint 1.1 (patch) — 2026-07-28

### Fixed
- Phát hiện khi Product Owner chạy thật trên **Windows 11**: `test_parse_ocr_ra_text` fail với
  `pytesseract.pytesseract.TesseractNotFoundError` vì Tesseract OCR (binary hệ điều hành) chưa
  được cài — README trước đó chỉ hướng dẫn cài qua Docker (đã có sẵn trong image), chưa hướng
  dẫn cài cho trường hợp chạy Parser Service trực tiếp trên Windows (ngoài Docker).

### Added
- `app/adapters/base.py`: exception mới `DependencyUnavailableError` — phân biệt lỗi hạ tầng
  (thiếu binary/dependency ngoài Python) với `ParsingError` (lỗi nội dung file).
- `ImageOcrAdapter.__init__(..., tesseract_cmd=None)` — cho phép trỏ thẳng đường dẫn
  `tesseract.exe` qua biến môi trường `PARSER_TESSERACT_CMD` (Config-driven), không bắt buộc
  sửa PATH hệ thống Windows.
- `main.py`: bắt riêng `DependencyUnavailableError` → trả HTTP 503 kèm hướng dẫn khắc phục,
  thay vì lộ traceback thô (500) như trước.
- 3 test case mới: `test_tesseract_cmd_cau_hinh_duoc_cho_windows`,
  `test_khong_tim_thay_tesseract_nem_dependency_unavailable_error` (adapter),
  `test_parse_thieu_tesseract_tra_503` (API) — tổng 35 test (từ 32).
- `README_SPRINT1.1.md` Mục 14: chuyển toàn bộ hướng dẫn sang Windows/PowerShell (theo yêu cầu
  người dùng), thêm Mục 0 hướng dẫn cài Tesseract OCR (UB-Mannheim build) + gói ngôn ngữ tiếng
  Việt cho Windows.
- `.env.example`: thêm `PARSER_TESSERACT_CMD` (để trống khi chạy qua Docker).

## [parser-service 0.1.0] — Sprint 1.1 — 2026-07-28

### Added
- Service Python/FastAPI mới `docker/ai-services/parser-service/` (theo ADR-001).
- `app/domain/parsed_document.py` — model chuẩn hoá `ParsedDocument`/`ParsedTable`/`ParsedImage`.
- `app/adapters/base.py` — interface `ParserAdapter` (Plugin Architecture) + `ParsingError`/`UnsupportedFileTypeError`.
- 6 adapter: `TextAdapter` (txt/md/html), `DocxAdapter`, `XlsxAdapter`, `PptxAdapter`, `PdfAdapter`, `ImageOcrAdapter` (eng+vie).
- `app/registry.py` — `ParserRegistry`, chống đăng ký trùng extension.
- `app/main.py` — `POST /parse`, `GET /parsers`, `GET /health`.
- 32 unit/integration test (fixture sinh động qua `conftest.py`, không commit file nhị phân).
- `Dockerfile` (cài `tesseract-ocr` + `tesseract-ocr-vie`), thêm service `parser-service` vào `docker-compose.yml`.
- CI/CD: job `lint-and-test-parser-service` + `build-image-parser-service` trong `ci-cd.yml`.

### Known gaps (chuyển sang Sprint 1.1b hoặc 1.2)
- CAD (DWG/DXF), Visio, Draw.io, Email (.eml/.msg), ZIP chưa có adapter — quyết định phạm vi có chủ đích.
- Chưa tích hợp thật với Document Manager (Gateway) để tự động gọi `/parse` khi có tài liệu mới.
- Chưa test với file thật của dự án (mới test bằng fixture tự sinh) và chưa xác nhận `docker compose up` trên máy có Docker daemon thật.

## [gateway 0.3.0] — Sprint 0.3 — 2026-07-28

### Added
- `lib/diContainer.js` — DI Container (awilix) với Module Registry Pattern (`registerService`).
- `lib/eventBus.js` + `domain/DomainEvent.js` — Event Bus pluggable transport
  (`InMemoryTransport` cho dev/test, `RedisStreamsTransport` cho production qua `EVENT_BUS_DRIVER`).
- `lib/logger.js` — logger tập trung (pino), phân kênh Application/Audit/Security/System/AI Usage.
- `routes/health.js`, `GET /api/health` — endpoint mẫu minh hoạ DI + Event Bus.
- Jest Testing Framework: 32 unit/integration test, coverage threshold cho `eventBus.js`/`diContainer.js`.
- ESLint config.
- `Dockerfile` multi-stage (development/production) cho Gateway.
- `docker-compose.yml` (service `redis`, `gateway`) + `docker-compose.override.yml` (dev).
- GitHub Actions `ci-cd.yml`: lint → test → build image → push (ghcr.io) → deploy staging (auto)
  → deploy production (Manual Approval).
- `docs/adr/ADR-001` đến `ADR-003` — chính thức hoá 3 quyết định kiến trúc đã phê duyệt.

### Changed
- Đổi tên quy ước Sprint: S1–S2 cũ (`INSTRUCTIONS.md`) → Sprint 0.1–0.2 (xem ADR-002, ADR-003).

### Known gaps (chuyển sang Sprint 1.1 hoặc khi có hạ tầng)
- 2 job `deploy-staging`/`deploy-production` trong CI/CD còn là placeholder, chờ thông tin hạ tầng thật.
- Chưa xác nhận `docker compose up -d --build` trên máy có Docker daemon thật (môi trường phát
  triển hiện tại không có Docker).

## [Sprint 0.1–0.2] — trước 2026-07-28 (đổi tên từ S1–S2, xem ADR-002)
- Portal GAS, Config Center, Project Manager, Document Manager đa nguồn, Synchronization Engine
  cơ bản. (Chi tiết: `INSTRUCTIONS.md`, chưa có CHANGELOG riêng — bổ sung hồi tố nếu cần.)

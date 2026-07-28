# ADR-002: Tiếp nối từ Sprint 0.1–0.2 đã hoàn thành, không khởi tạo lại từ đầu

Ngày: 2026-07-28 | Trạng thái: **Accepted**

## Bối cảnh
Prompt khởi động mô tả Giai đoạn 1 ("Khởi tạo dự án": Repository, Docker, Core Framework,
Logging, DI, Event Bus, Testing Framework, CI/CD) như thể dự án bắt đầu từ số 0. Trong khi đó
`INSTRUCTIONS.md` xác nhận Sprint 1–2 (Portal GAS, Config Center, Project Manager, Document
Manager đa nguồn, Synchronization Engine cơ bản) **đã hoàn thành**.

## Quyết định
- Đổi tên Sprint 1–2 cũ thành **Sprint 0.1–0.2 (Foundation)**, giữ nguyên trạng thái Done.
- Development Master Plan v1.0 (Mục 2, 3) tiếp nối từ trạng thái hiện tại: Giai đoạn 1 chỉ còn
  cần bổ sung phần **chưa có**: CI/CD, Event Bus, Testing Framework, DI Container — đây chính là
  phạm vi Sprint 0.3.
- Không tổ chức lại thư mục `pwp/gas/` và `pwp/docker/gateway/` đã có; Sprint 0.3 chỉ **thêm**
  file mới vào các thư mục `lib/`, `tests/`, `.github/workflows/`.

## Hệ quả
**Được:** không mất công sức đã đầu tư ở Sprint 0.1–0.2; giữ tính liên tục lịch sử Git/tag.
**Mất:** cần tài liệu hoá rõ ràng bảng ánh xạ Giai đoạn ↔ Sprint (đã có ở Master Plan Mục 2) để
tránh nhầm lẫn giữa 2 cách đánh số cũ/mới khi có thành viên mới tham gia dự án.

## Phương án đã cân nhắc nhưng không chọn
- **Archive code cũ, khởi tạo repo mới đúng theo Giai đoạn 1 của Prompt khởi động**: bị loại vì
  lãng phí, vi phạm trực tiếp nguyên tắc "ưu tiên mở rộng thay vì sửa" và "hạn chế Breaking Change".

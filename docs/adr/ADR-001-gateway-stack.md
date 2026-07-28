# ADR-001: Giữ Node.js/Express cho Gateway, dùng Python/FastAPI cho AI services

Ngày: 2026-07-28 | Trạng thái: **Accepted**

## Bối cảnh
`INSTRUCTIONS.md` mô tả Gateway đã được build bằng Node.js/Express từ Sprint 1–2 (nay là
Sprint 0.1–0.2) và đang hoạt động ổn định. Master Project Instructions lại liệt kê FastAPI
(Python) là công nghệ backend ưu tiên. Hai nguồn tài liệu không thống nhất về ngôn ngữ backend.

## Quyết định
- **Gateway (routing, auth, rate-limit, module router, logging)**: giữ nguyên Node.js/Express
  đã có, không viết lại. Đúng nguyên tắc "ưu tiên mở rộng thay vì sửa" (Mục II Prompt khởi động).
- **AI/ML services nặng** (Document Parser, Embedding, Knowledge/Vector/Graph orchestration,
  Agent Framework) mới ở Giai đoạn 4–5: viết bằng **Python/FastAPI**, chạy như service Docker
  riêng biệt (`docker/ai-services/`), giao tiếp với Gateway qua REST nội bộ hoặc message queue.

## Hệ quả
**Được:**
- Không tốn công viết lại phần Gateway đã chạy tốt.
- Python có hệ sinh thái AI/ML mạnh hơn (embedding, OCR, NLP libraries) cho các service mới.
- Ranh giới Clean Architecture rõ ràng hơn: Gateway = Interface Adapter/routing, AI services =
  Application/Domain xử lý nặng.

**Mất:**
- Vận hành 2 stack ngôn ngữ (Node + Python) làm tăng độ phức tạp CI/CD, cần 2 bộ pipeline lint/test.
- Cần chuẩn hoá giao tiếp nội bộ giữa 2 stack (REST contract hoặc message schema) để tránh lệch pha.

## Phương án đã cân nhắc nhưng không chọn
- **Viết lại toàn bộ Gateway bằng FastAPI**: bị loại vì vi phạm nguyên tắc hạn chế breaking
  change, tốn thời gian không cần thiết cho phần đã ổn định.
- **Chỉ dùng Node.js cho mọi service kể cả AI**: bị loại vì thiếu thư viện AI/ML trưởng thành so
  với Python, sẽ phải tự viết nhiều thứ Python đã có sẵn (embedding clients, OCR, PDF parsing nâng cao).

# Changelog

Định dạng dựa trên [Keep a Changelog](https://keepachangelog.com/), quy ước version theo
[Master Plan Mục 9](docs adr — release strategy): MAJOR.MINOR.PATCH cho mỗi service Docker.

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

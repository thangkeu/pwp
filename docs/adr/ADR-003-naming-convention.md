# ADR-003: Thống nhất cấu trúc đặt tên Giai đoạn → Sprint → Module → Task

Ngày: 2026-07-28 | Trạng thái: **Accepted**

## Bối cảnh
`INSTRUCTIONS.md` đánh số Sprint S1–S6 theo nhóm chức năng lớn. Prompt khởi động lại tổ chức
theo Giai đoạn (Phase) → Module → Task không giới hạn số Sprint. Dùng lẫn 2 cách gây khó theo dõi
tiến độ và khó tham chiếu chéo giữa các tài liệu.

## Quyết định
Từ nay dùng thống nhất 1 cấu trúc 4 cấp:

```
Giai đoạn (Phase, GĐ1..GĐ7)
  └── Sprint (2 tuần, đánh số <phase>.<seq>, vd: Sprint 0.3, Sprint 1.1, Sprint 4.2)
        └── Module (1 khối chức năng độc lập, vd: Event Bus, Parser)
              └── Task (đơn vị công việc cụ thể trong 1 Sprint)
```

Sprint 1–2 cũ (`INSTRUCTIONS.md`) → đổi thành Sprint 0.1–0.2 (xem ADR-002).
Sprint 3–6 cũ → ánh xạ sang Sprint 1.x–5.x theo bảng ở Master Plan Mục 2.

## Hệ quả
**Được:** mọi tài liệu (CHANGELOG, README Sprint, ADR, PR title) tham chiếu Sprint theo cùng 1
quy ước, dễ tra cứu, dễ tự động hoá (vd: gắn tag Git `sprint-X.Y`).
**Mất:** cần rà soát và cập nhật lại các chỗ trong `INSTRUCTIONS.md`/`SPRINT_PLAN.md` còn dùng
số Sprint cũ (S1–S6) — thực hiện dần khi các tài liệu đó được chỉnh sửa, không bắt buộc sửa toàn
bộ ngay lập tức.

## Phương án đã cân nhắc nhưng không chọn
- **Giữ nguyên 2 cách đánh số song song, chỉ ghi chú quy đổi**: bị loại vì dễ gây nhầm lẫn về
  lâu dài khi số lượng Sprint tăng lên, đặc biệt khi có thành viên mới tham gia dự án.

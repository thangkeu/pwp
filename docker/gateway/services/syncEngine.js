'use strict';

const { DomainEvent } = require('../domain/DomainEvent');

/**
 * @typedef {Object} SyncSummary
 * @property {number} created
 * @property {number} updated
 * @property {number} deleted
 * @property {number} moved
 * @property {number} unchanged
 */

/**
 * SyncEngine — logic diff DUY NHẤT của toàn hệ thống (INSTRUCTIONS.md Nguyên tắc 5: "Đồng bộ
 * là diff, không phải overwrite"). Không phụ thuộc connector nào là Google Drive hay Microsoft
 * Graph — chỉ làm việc với `DocumentItem` chuẩn hoá.
 *
 * Sprint 1.2 nâng cấp: trước đây (Sprint 0.1–0.2) mọi lần sync là "full scan" (connector trả về
 * TOÀN BỘ danh sách hiện có, engine tự suy ra deleted bằng cách so sánh với bản ghi cũ). Từ
 * Sprint 1.2, connector có thể trả `mode: 'delta'` (chỉ gồm các item THAY ĐỔI kể từ lần sync
 * trước, do chính API nguồn — Google Changes API / Microsoft Graph delta query — xác định).
 * Engine xử lý đúng ngữ nghĩa của từng mode, KHÔNG trộn lẫn 2 logic.
 */
class SyncEngine {
  /**
   * @param {Object} deps
   * @param {import('../repositories/documentRepository').InMemoryDocumentRepository} deps.repository
   * @param {import('../lib/eventBus').EventBus} deps.eventBus
   * @param {import('pino').Logger} [deps.logger=console]
   */
  constructor({ repository, eventBus, logger = console }) {
    this._repository = repository;
    this._eventBus = eventBus;
    this._logger = logger;
  }

  /**
   * Đồng bộ danh sách item của 1 nguồn dữ liệu.
   *
   * @param {string} sourceId - ID của source trong bảng `sources`
   * @param {{mode: 'full'|'delta', items: import('../domain/DocumentItem').DocumentItem[]}} scanResult
   *   - mode 'full': `items` là TOÀN BỘ item hiện có tại nguồn (không phải batch).
   *   - mode 'delta': `items` chỉ gồm item đã thay đổi (created/updated/moved) hoặc bị xoá
   *     (đánh dấu `removed: true`), do connector delta xác định.
   * @returns {Promise<SyncSummary>} Thống kê created/updated/deleted/moved/unchanged
   * @throws {Error} Khi transaction lưu trữ thất bại, hoặc `scanResult.mode` không hợp lệ
   */
  async syncSourceItems(sourceId, scanResult) {
    if (!sourceId) {
      throw new TypeError('syncSourceItems yêu cầu sourceId');
    }
    if (!scanResult || !Array.isArray(scanResult.items)) {
      throw new TypeError('syncSourceItems yêu cầu scanResult.items là mảng DocumentItem');
    }

    if (scanResult.mode === 'full') {
      return this._reconcileFullScan(sourceId, scanResult.items);
    }
    if (scanResult.mode === 'delta') {
      return this._applyDelta(sourceId, scanResult.items);
    }
    throw new TypeError(`scanResult.mode không hợp lệ: "${scanResult.mode}" (chỉ nhận 'full' hoặc 'delta')`);
  }

  /**
   * Chế độ full-scan: so sánh TOÀN BỘ danh sách mới quét với bản ghi cũ, tự suy ra
   * created/updated/deleted/moved/unchanged. Dùng cho lần sync ĐẦU TIÊN của 1 source (chưa có
   * pageToken/deltaLink) hoặc khi cần baseline reconciliation định kỳ.
   *
   * @private
   */
  async _reconcileFullScan(sourceId, items) {
    const stored = await this._repository.listBySource(sourceId);
    const storedById = new Map(stored.map((doc) => [doc.externalId, doc]));
    const scannedIds = new Set(items.map((item) => item.externalId));

    const summary = { created: 0, updated: 0, deleted: 0, moved: 0, unchanged: 0 };

    for (const item of items) {
      const existing = storedById.get(item.externalId);
      if (!existing) {
        await this._create(sourceId, item, summary);
        continue;
      }
      await this._compareAndUpdate(sourceId, existing, item, summary);
    }

    for (const existing of stored) {
      if (!scannedIds.has(existing.externalId)) {
        await this._delete(sourceId, existing.externalId, summary);
      }
    }

    this._logger.info?.({ sourceId, summary }, 'SyncEngine: hoàn tất full-scan reconciliation');
    return summary;
  }

  /**
   * Chế độ delta: áp dụng trực tiếp từng item connector đã xác định là thay đổi/xoá — KHÔNG
   * suy luận deleted bằng cách so sánh toàn bộ danh sách (vì `items` ở đây chỉ là phần thay đổi,
   * không phải toàn bộ trạng thái nguồn).
   *
   * @private
   */
  async _applyDelta(sourceId, items) {
    const summary = { created: 0, updated: 0, deleted: 0, moved: 0, unchanged: 0 };

    for (const item of items) {
      if (item.removed) {
        await this._delete(sourceId, item.externalId, summary);
        continue;
      }
      const existing = (await this._repository.listBySource(sourceId)).find(
        (doc) => doc.externalId === item.externalId
      );
      if (!existing) {
        await this._create(sourceId, item, summary);
        continue;
      }
      await this._compareAndUpdate(sourceId, existing, item, summary);
    }

    this._logger.info?.({ sourceId, summary }, 'SyncEngine: hoàn tất delta apply');
    return summary;
  }

  /** @private */
  async _create(sourceId, item, summary) {
    await this._repository.upsert(sourceId, item);
    await this._logAndPublish(sourceId, 'created', item);
    summary.created += 1;
  }

  /** @private */
  async _delete(sourceId, externalId, summary) {
    await this._repository.remove(sourceId, externalId);
    await this._logAndPublish(sourceId, 'deleted', { externalId });
    summary.deleted += 1;
  }

  /**
   * So sánh 1 item đã tồn tại với bản quét mới: phân biệt "updated" (nội dung đổi, theo
   * contentHash) và "moved" (chỉ đổi path/name, nội dung giữ nguyên) — 2 loại sự kiện khác
   * nhau có ý nghĩa nghiệp vụ khác nhau (Metadata Engine chỉ cần re-embed khi "updated" thật,
   * không cần khi chỉ "moved").
   * @private
   */
  async _compareAndUpdate(sourceId, existing, item, summary) {
    const contentChanged = existing.contentHash !== item.contentHash;
    const pathChanged = existing.path !== item.path || existing.name !== item.name;

    if (!contentChanged && !pathChanged) {
      summary.unchanged += 1;
      return;
    }

    await this._repository.upsert(sourceId, item);

    if (contentChanged) {
      await this._logAndPublish(sourceId, 'updated', item);
      summary.updated += 1;
    } else {
      await this._logAndPublish(sourceId, 'moved', item, { fromPath: existing.path });
      summary.moved += 1;
    }
  }

  /** @private */
  async _logAndPublish(sourceId, changeType, item, extraPayload = {}) {
    const occurredAt = new Date().toISOString();
    await this._repository.appendSyncLog(sourceId, { changeType, externalId: item.externalId, occurredAt });

    if (this._eventBus) {
      await this._eventBus.publish(
        new DomainEvent(
          `document.sync.${changeType}`,
          { sourceId, ...item, ...extraPayload },
          { source: 'SyncEngine' }
        )
      );
    }
  }
}

module.exports = { SyncEngine };

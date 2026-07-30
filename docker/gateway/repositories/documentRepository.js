'use strict';

/**
 * DocumentRepository — interface mà `syncEngine.js` phụ thuộc vào (Dependency Inversion,
 * INSTRUCTIONS.md Phần IV.2 mục D). Bất kỳ implementation nào (Postgres, In-Memory cho test)
 * đều phải cung cấp đủ 4 method dưới đây với đúng chữ ký.
 *
 * @interface DocumentRepository
 */

/**
 * InMemoryDocumentRepository — implementation dùng cho unit test và demo local, KHÔNG dùng
 * production (không persist qua restart). PostgresDocumentRepository (Sprint sau) implement
 * cùng interface này, `syncEngine.js` không cần sửa gì khi đổi sang Postgres thật.
 */
class InMemoryDocumentRepository {
  constructor() {
    /** @type {Map<string, Map<string, object>>} sourceId -> (externalId -> storedRecord) */
    this._bySource = new Map();
    /** @type {Map<string, object[]>} sourceId -> sync_log entries */
    this._syncLogBySource = new Map();
  }

  /**
   * @param {string} sourceId
   * @returns {Promise<object[]>} Bản ghi tài liệu đã lưu (dạng {externalId, name, path, contentHash, ...})
   */
  async listBySource(sourceId) {
    const map = this._bySource.get(sourceId);
    return map ? Array.from(map.values()) : [];
  }

  /**
   * @param {string} sourceId
   * @param {import('../domain/DocumentItem').DocumentItem} item
   * @returns {Promise<void>}
   */
  async upsert(sourceId, item) {
    if (!this._bySource.has(sourceId)) {
      this._bySource.set(sourceId, new Map());
    }
    this._bySource.get(sourceId).set(item.externalId, { ...item });
  }

  /**
   * @param {string} sourceId
   * @param {string} externalId
   * @returns {Promise<void>}
   */
  async remove(sourceId, externalId) {
    this._bySource.get(sourceId)?.delete(externalId);
  }

  /**
   * @param {string} sourceId
   * @param {{changeType: string, externalId: string, occurredAt: string}} entry
   * @returns {Promise<void>}
   */
  async appendSyncLog(sourceId, entry) {
    if (!this._syncLogBySource.has(sourceId)) {
      this._syncLogBySource.set(sourceId, []);
    }
    this._syncLogBySource.get(sourceId).push(entry);
  }

  /** Helper chỉ dùng cho test — không thuộc interface chính thức. */
  async getSyncLog(sourceId) {
    return this._syncLogBySource.get(sourceId) || [];
  }
}

module.exports = { InMemoryDocumentRepository };

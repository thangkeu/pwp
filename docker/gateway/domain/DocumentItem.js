'use strict';

/**
 * DocumentItem — định dạng chuẩn hoá DUY NHẤT mà mọi connector (Google Drive, Microsoft Graph,
 * GitHub, S3...) phải trả về, bất kể nguồn dữ liệu là gì (INSTRUCTIONS.md Phần II.3:
 * "connector chỉ có 1 nhiệm vụ — quét ra danh sách chuẩn hoá... Logic diff/lưu trữ nằm 100%
 * trong Synchronization Engine, connector không được viết logic diff riêng").
 */
class DocumentItem {
  /**
   * @param {Object} fields
   * @param {string} fields.externalId - ID duy nhất tại nguồn (vd: Google Drive fileId, Graph driveItem id)
   * @param {string} fields.name
   * @param {string} fields.path - Đường dẫn logic (vd: "/Dự án ABC/Proposal/baogia.docx")
   * @param {string} fields.mimeType
   * @param {number} fields.sizeBytes
   * @param {string} fields.contentHash - Dùng để phát hiện thay đổi nội dung thật (không chỉ đổi tên)
   * @param {string} fields.webUrl
   * @param {boolean} [fields.removed=false] - true nếu connector delta báo item đã bị xoá tại nguồn
   * @throws {TypeError} Khi thiếu field bắt buộc
   */
  constructor({ externalId, name, path, mimeType, sizeBytes, contentHash, webUrl, removed = false }) {
    const required = { externalId, name, path };
    for (const [key, value] of Object.entries(required)) {
      if (typeof value !== 'string' || value.length === 0) {
        throw new TypeError(`DocumentItem.${key} phải là chuỗi không rỗng`);
      }
    }
    this.externalId = externalId;
    this.name = name;
    this.path = path;
    this.mimeType = mimeType || 'application/octet-stream';
    this.sizeBytes = typeof sizeBytes === 'number' ? sizeBytes : 0;
    this.contentHash = contentHash || null;
    this.webUrl = webUrl || null;
    this.removed = Boolean(removed);
  }
}

module.exports = { DocumentItem };

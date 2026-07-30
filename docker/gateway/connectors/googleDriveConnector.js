'use strict';

const { DocumentItem } = require('../domain/DocumentItem');

/**
 * GoogleDriveConnector — quét Google Drive, ưu tiên Delta API (`changes.list`) thay vì quét đệ
 * quy toàn bộ folder (baseline đơn giản ở Sprint 0.1–0.2). INSTRUCTIONS.md 6.5:
 * "dùng `Drive.Changes.list` với `pageToken`... thay vì luôn quét đệ quy toàn bộ folder".
 *
 * Nguyên tắc bất biến (INSTRUCTIONS.md 2.3): connector CHỈ quét ra danh sách `DocumentItem`
 * chuẩn hoá, KHÔNG tự viết logic diff — điều đó thuộc về `SyncEngine`.
 */
class GoogleDriveConnector {
  /**
   * @param {Object} deps
   * @param {() => Promise<string>} deps.accessTokenProvider - Lấy OAuth access token hiện hành
   * @param {typeof fetch} [deps.fetchImpl=fetch] - Cho phép inject fetch giả lập khi unit test
   * @param {string} [deps.apiBaseUrl='https://www.googleapis.com/drive/v3']
   */
  constructor({ accessTokenProvider, fetchImpl = fetch, apiBaseUrl = 'https://www.googleapis.com/drive/v3' }) {
    this._accessTokenProvider = accessTokenProvider;
    this._fetch = fetchImpl;
    this._apiBaseUrl = apiBaseUrl;
  }

  /**
   * @param {Object} options
   * @param {string|null} [options.storedPageToken] - `pageToken` lưu từ lần sync trước (null = lần đầu)
   * @returns {Promise<{mode: 'full'|'delta', items: DocumentItem[], nextPageToken: string}>}
   * @throws {Error} Khi gọi Google Drive API thất bại (fail gracefully — caller phải log/xử lý)
   */
  async scan({ storedPageToken = null } = {}) {
    const token = await this._accessTokenProvider();

    if (!storedPageToken) {
      return this._fullScan(token);
    }
    return this._deltaScan(token, storedPageToken);
  }

  /** @private Lần đầu: chưa có pageToken — quét toàn bộ + lấy startPageToken cho lần sau. */
  async _fullScan(token) {
    const items = [];
    let pageToken = null;

    do {
      const url = new URL(`${this._apiBaseUrl}/files`);
      url.searchParams.set('q', 'trashed = false');
      url.searchParams.set(
        'fields',
        'nextPageToken, files(id, name, mimeType, size, md5Checksum, webViewLink, parents)'
      );
      if (pageToken) url.searchParams.set('pageToken', pageToken);

      const response = await this._authorizedFetch(url.toString(), token);
      const body = await this._parseJsonOrThrow(response, 'files.list');

      for (const file of body.files || []) {
        items.push(this._toDocumentItem(file));
      }
      pageToken = body.nextPageToken || null;
    } while (pageToken);

    const startTokenResponse = await this._authorizedFetch(
      `${this._apiBaseUrl}/changes/startPageToken`,
      token
    );
    const startTokenBody = await this._parseJsonOrThrow(startTokenResponse, 'changes.getStartPageToken');

    return { mode: 'full', items, nextPageToken: startTokenBody.startPageToken };
  }

  /** @private Đã có pageToken — chỉ lấy phần THAY ĐỔI kể từ lần trước. */
  async _deltaScan(token, storedPageToken) {
    const items = [];
    let pageToken = storedPageToken;
    let newStartPageToken = null;

    do {
      const url = new URL(`${this._apiBaseUrl}/changes`);
      url.searchParams.set('pageToken', pageToken);
      url.searchParams.set(
        'fields',
        'nextPageToken, newStartPageToken, changes(fileId, removed, file(id, name, mimeType, size, md5Checksum, webViewLink, parents))'
      );

      const response = await this._authorizedFetch(url.toString(), token);
      const body = await this._parseJsonOrThrow(response, 'changes.list');

      for (const change of body.changes || []) {
        if (change.removed || !change.file) {
          items.push(new DocumentItem({
            externalId: change.fileId,
            name: '(removed)',
            path: '(removed)',
            removed: true,
          }));
        } else {
          items.push(this._toDocumentItem(change.file));
        }
      }

      pageToken = body.nextPageToken || null;
      if (body.newStartPageToken) newStartPageToken = body.newStartPageToken;
    } while (pageToken);

    return { mode: 'delta', items, nextPageToken: newStartPageToken };
  }

  /** @private */
  _toDocumentItem(file) {
    return new DocumentItem({
      externalId: file.id,
      name: file.name,
      path: `/${file.name}`, // Path đầy đủ theo parents cần Sprint sau (cần thêm 1 lượt resolve tên folder cha)
      mimeType: file.mimeType,
      sizeBytes: file.size ? Number(file.size) : 0,
      contentHash: file.md5Checksum || null,
      webUrl: file.webViewLink || null,
    });
  }

  /** @private */
  async _authorizedFetch(url, token) {
    return this._fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  }

  /** @private */
  async _parseJsonOrThrow(response, operation) {
    if (!response.ok) {
      const body = await response.text().catch(() => '');
      throw new Error(`Google Drive API lỗi ở ${operation}: HTTP ${response.status} — ${body}`);
    }
    return response.json();
  }
}

module.exports = { GoogleDriveConnector };

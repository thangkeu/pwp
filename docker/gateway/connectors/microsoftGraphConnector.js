'use strict';

const { DocumentItem } = require('../domain/DocumentItem');

/**
 * MicrosoftGraphConnector — quét OneDrive/SharePoint qua Microsoft Graph Delta Query
 * (INSTRUCTIONS.md 6.5: endpoint `/me/drive/root/delta`, theo dõi `@odata.deltaLink`).
 *
 * Cùng nguyên tắc bất biến với GoogleDriveConnector: chỉ trả `DocumentItem` chuẩn hoá,
 * không tự viết logic diff.
 */
class MicrosoftGraphConnector {
  /**
   * @param {Object} deps
   * @param {() => Promise<string>} deps.accessTokenProvider - OAuth2 Client Credentials token (INSTRUCTIONS.md 8.4)
   * @param {typeof fetch} [deps.fetchImpl=fetch]
   * @param {string} [deps.apiBaseUrl='https://graph.microsoft.com/v1.0']
   * @param {string} [deps.driveRootPath='/me/drive/root']
   */
  constructor({
    accessTokenProvider,
    fetchImpl = fetch,
    apiBaseUrl = 'https://graph.microsoft.com/v1.0',
    driveRootPath = '/me/drive/root',
  }) {
    this._accessTokenProvider = accessTokenProvider;
    this._fetch = fetchImpl;
    this._apiBaseUrl = apiBaseUrl;
    this._driveRootPath = driveRootPath;
  }

  /**
   * @param {Object} options
   * @param {string|null} [options.storedDeltaLink] - `@odata.deltaLink` lưu từ lần sync trước (null = lần đầu)
   * @returns {Promise<{mode: 'full'|'delta', items: DocumentItem[], nextDeltaLink: string}>}
   * @throws {Error} Khi gọi Microsoft Graph API thất bại
   */
  async scan({ storedDeltaLink = null } = {}) {
    const token = await this._accessTokenProvider();
    const isFirstSync = !storedDeltaLink;
    let url = storedDeltaLink || `${this._apiBaseUrl}${this._driveRootPath}/delta`;

    const items = [];
    let nextDeltaLink = null;

    do {
      const response = await this._fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!response.ok) {
        const body = await response.text().catch(() => '');
        throw new Error(`Microsoft Graph delta query lỗi: HTTP ${response.status} — ${body}`);
      }
      const body = await response.json();

      for (const driveItem of body.value || []) {
        items.push(this._toDocumentItem(driveItem));
      }

      url = body['@odata.nextLink'] || null;
      if (body['@odata.deltaLink']) {
        nextDeltaLink = body['@odata.deltaLink'];
      }
    } while (url);

    return { mode: isFirstSync ? 'full' : 'delta', items, nextDeltaLink };
  }

  /** @private */
  _toDocumentItem(driveItem) {
    if (driveItem.deleted) {
      return new DocumentItem({
        externalId: driveItem.id,
        name: '(removed)',
        path: '(removed)',
        removed: true,
      });
    }
    const parentPath = driveItem.parentReference?.path || '';
    return new DocumentItem({
      externalId: driveItem.id,
      name: driveItem.name,
      path: `${parentPath}/${driveItem.name}`,
      mimeType: driveItem.file?.mimeType || (driveItem.folder ? 'application/vnd.folder' : 'application/octet-stream'),
      sizeBytes: driveItem.size || 0,
      contentHash: driveItem.file?.hashes?.quickXorHash || null,
      webUrl: driveItem.webUrl || null,
    });
  }
}

module.exports = { MicrosoftGraphConnector };

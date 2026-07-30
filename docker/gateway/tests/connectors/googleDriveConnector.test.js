'use strict';

const { GoogleDriveConnector } = require('../../connectors/googleDriveConnector');

function jsonResponse(body, ok = true, status = 200) {
  return {
    ok,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

describe('GoogleDriveConnector', () => {
  test('lần đầu (không có storedPageToken): full scan + trả startPageToken cho lần sau', async () => {
    const fetchImpl = jest
      .fn()
      // 1. files.list (1 trang duy nhất)
      .mockResolvedValueOnce(
        jsonResponse({
          files: [
            { id: 'f1', name: 'baogia.docx', mimeType: 'application/vnd...docx', size: '1024', md5Checksum: 'h1' },
          ],
        })
      )
      // 2. changes/startPageToken
      .mockResolvedValueOnce(jsonResponse({ startPageToken: 'TOKEN_1' }));

    const connector = new GoogleDriveConnector({
      accessTokenProvider: async () => 'fake-token',
      fetchImpl,
    });

    const result = await connector.scan({ storedPageToken: null });

    expect(result.mode).toBe('full');
    expect(result.items).toHaveLength(1);
    expect(result.items[0].externalId).toBe('f1');
    expect(result.items[0].contentHash).toBe('h1');
    expect(result.nextPageToken).toBe('TOKEN_1');
  });

  test('full scan phân trang đúng (nhiều page files.list)', async () => {
    const fetchImpl = jest
      .fn()
      .mockResolvedValueOnce(jsonResponse({ files: [{ id: 'f1', name: 'a' }], nextPageToken: 'PAGE_2' }))
      .mockResolvedValueOnce(jsonResponse({ files: [{ id: 'f2', name: 'b' }] }))
      .mockResolvedValueOnce(jsonResponse({ startPageToken: 'TOKEN_X' }));

    const connector = new GoogleDriveConnector({ accessTokenProvider: async () => 't', fetchImpl });
    const result = await connector.scan({ storedPageToken: null });

    expect(result.items.map((i) => i.externalId)).toEqual(['f1', 'f2']);
    expect(fetchImpl).toHaveBeenCalledTimes(3);
  });

  test('có storedPageToken: gọi changes.list (delta), không gọi lại files.list', async () => {
    const fetchImpl = jest.fn().mockResolvedValueOnce(
      jsonResponse({
        changes: [
          { fileId: 'f1', file: { id: 'f1', name: 'a-updated', md5Checksum: 'h2' } },
          { fileId: 'f2', removed: true },
        ],
        newStartPageToken: 'TOKEN_2',
      })
    );

    const connector = new GoogleDriveConnector({ accessTokenProvider: async () => 't', fetchImpl });
    const result = await connector.scan({ storedPageToken: 'TOKEN_1' });

    expect(result.mode).toBe('delta');
    expect(result.items).toHaveLength(2);
    expect(result.items[1].removed).toBe(true);
    expect(result.nextPageToken).toBe('TOKEN_2');
    expect(fetchImpl).toHaveBeenCalledTimes(1);
    expect(fetchImpl.mock.calls[0][0]).toContain('/changes');
  });

  test('ném lỗi rõ ràng khi Google API trả lỗi HTTP (fail gracefully, không nuốt lỗi)', async () => {
    const fetchImpl = jest.fn().mockResolvedValueOnce(jsonResponse({ error: 'quota exceeded' }, false, 429));
    const connector = new GoogleDriveConnector({ accessTokenProvider: async () => 't', fetchImpl });

    await expect(connector.scan({ storedPageToken: null })).rejects.toThrow(/HTTP 429/);
  });
});

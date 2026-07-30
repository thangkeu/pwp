'use strict';

const { MicrosoftGraphConnector } = require('../../connectors/microsoftGraphConnector');

function jsonResponse(body, ok = true, status = 200) {
  return {
    ok,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}

describe('MicrosoftGraphConnector', () => {
  test('lần đầu (không có storedDeltaLink): mode full, trả deltaLink cuối cùng', async () => {
    const fetchImpl = jest.fn().mockResolvedValueOnce(
      jsonResponse({
        value: [
          {
            id: 'd1',
            name: 'baogia.docx',
            size: 2048,
            file: { mimeType: 'application/vnd...docx', hashes: { quickXorHash: 'hx1' } },
            parentReference: { path: '/drive/root:/Du an ABC' },
            webUrl: 'https://onedrive.com/d1',
          },
        ],
        '@odata.deltaLink': 'https://graph.microsoft.com/delta?token=T1',
      })
    );

    const connector = new MicrosoftGraphConnector({ accessTokenProvider: async () => 't', fetchImpl });
    const result = await connector.scan({ storedDeltaLink: null });

    expect(result.mode).toBe('full');
    expect(result.items).toHaveLength(1);
    expect(result.items[0].externalId).toBe('d1');
    expect(result.items[0].path).toBe('/drive/root:/Du an ABC/baogia.docx');
    expect(result.nextDeltaLink).toBe('https://graph.microsoft.com/delta?token=T1');
  });

  test('có storedDeltaLink: mode delta, gọi thẳng deltaLink đã lưu (không gọi /delta gốc)', async () => {
    const fetchImpl = jest.fn().mockResolvedValueOnce(
      jsonResponse({
        value: [{ id: 'd1', deleted: {} }],
        '@odata.deltaLink': 'https://graph.microsoft.com/delta?token=T2',
      })
    );

    const connector = new MicrosoftGraphConnector({ accessTokenProvider: async () => 't', fetchImpl });
    const result = await connector.scan({ storedDeltaLink: 'https://graph.microsoft.com/delta?token=T1' });

    expect(result.mode).toBe('delta');
    expect(fetchImpl).toHaveBeenCalledWith(
      'https://graph.microsoft.com/delta?token=T1',
      expect.anything()
    );
    expect(result.items[0].removed).toBe(true);
  });

  test('theo đúng @odata.nextLink qua nhiều trang trước khi tới deltaLink cuối', async () => {
    const fetchImpl = jest
      .fn()
      .mockResolvedValueOnce(
        jsonResponse({
          value: [{ id: 'd1', name: 'a', parentReference: {} }],
          '@odata.nextLink': 'https://graph.microsoft.com/delta?page=2',
        })
      )
      .mockResolvedValueOnce(
        jsonResponse({
          value: [{ id: 'd2', name: 'b', parentReference: {} }],
          '@odata.deltaLink': 'https://graph.microsoft.com/delta?token=FINAL',
        })
      );

    const connector = new MicrosoftGraphConnector({ accessTokenProvider: async () => 't', fetchImpl });
    const result = await connector.scan({ storedDeltaLink: null });

    expect(result.items.map((i) => i.externalId)).toEqual(['d1', 'd2']);
    expect(result.nextDeltaLink).toBe('https://graph.microsoft.com/delta?token=FINAL');
    expect(fetchImpl).toHaveBeenCalledTimes(2);
  });

  test('ném lỗi rõ ràng khi Graph API trả lỗi HTTP', async () => {
    const fetchImpl = jest.fn().mockResolvedValueOnce(jsonResponse({ error: 'unauthorized' }, false, 401));
    const connector = new MicrosoftGraphConnector({ accessTokenProvider: async () => 't', fetchImpl });

    await expect(connector.scan({ storedDeltaLink: null })).rejects.toThrow(/HTTP 401/);
  });

  test('folder (không phải file) vẫn map đúng mimeType mặc định', async () => {
    const fetchImpl = jest.fn().mockResolvedValueOnce(
      jsonResponse({
        value: [{ id: 'd1', name: 'ThuMuc', folder: {}, parentReference: {} }],
        '@odata.deltaLink': 'https://graph.microsoft.com/delta?token=T1',
      })
    );
    const connector = new MicrosoftGraphConnector({ accessTokenProvider: async () => 't', fetchImpl });
    const result = await connector.scan({ storedDeltaLink: null });

    expect(result.items[0].mimeType).toBe('application/vnd.folder');
  });
});

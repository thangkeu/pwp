'use strict';

const { SyncEngine } = require('../../services/syncEngine');
const { InMemoryDocumentRepository } = require('../../repositories/documentRepository');
const { EventBus, InMemoryTransport } = require('../../lib/eventBus');
const { DocumentItem } = require('../../domain/DocumentItem');

function makeSilentLogger() {
  return { error: jest.fn(), warn: jest.fn(), info: jest.fn() };
}

function makeSyncEngine() {
  const repository = new InMemoryDocumentRepository();
  const eventBus = new EventBus(new InMemoryTransport(), makeSilentLogger());
  const engine = new SyncEngine({ repository, eventBus, logger: makeSilentLogger() });
  return { engine, repository, eventBus };
}

describe('SyncEngine — full-scan reconciliation', () => {
  test('lần đầu sync: mọi item đều là created', async () => {
    const { engine, repository } = makeSyncEngine();
    const items = [
      new DocumentItem({ externalId: 'a', name: 'a.docx', path: '/a.docx', contentHash: 'h1' }),
      new DocumentItem({ externalId: 'b', name: 'b.docx', path: '/b.docx', contentHash: 'h2' }),
    ];

    const summary = await engine.syncSourceItems('source-1', { mode: 'full', items });

    expect(summary).toEqual({ created: 2, updated: 0, deleted: 0, moved: 0, unchanged: 0 });
    expect(await repository.listBySource('source-1')).toHaveLength(2);
  });

  test('sync lần 2 với đúng dữ liệu cũ: toàn bộ unchanged', async () => {
    const { engine } = makeSyncEngine();
    const items = [new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h1' })];

    await engine.syncSourceItems('source-1', { mode: 'full', items });
    const summary2 = await engine.syncSourceItems('source-1', { mode: 'full', items });

    expect(summary2).toEqual({ created: 0, updated: 0, deleted: 0, moved: 0, unchanged: 1 });
  });

  test('contentHash đổi -> updated', async () => {
    const { engine } = makeSyncEngine();
    await engine.syncSourceItems('source-1', {
      mode: 'full',
      items: [new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h1' })],
    });

    const summary = await engine.syncSourceItems('source-1', {
      mode: 'full',
      items: [new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h2' })],
    });

    expect(summary).toEqual({ created: 0, updated: 1, deleted: 0, moved: 0, unchanged: 0 });
  });

  test('chỉ đổi path (contentHash giữ nguyên) -> moved, không phải updated', async () => {
    const { engine } = makeSyncEngine();
    await engine.syncSourceItems('source-1', {
      mode: 'full',
      items: [new DocumentItem({ externalId: 'a', name: 'a', path: '/old/a', contentHash: 'h1' })],
    });

    const summary = await engine.syncSourceItems('source-1', {
      mode: 'full',
      items: [new DocumentItem({ externalId: 'a', name: 'a', path: '/new/a', contentHash: 'h1' })],
    });

    expect(summary).toEqual({ created: 0, updated: 0, deleted: 0, moved: 1, unchanged: 0 });
  });

  test('item biến mất khỏi danh sách quét mới -> deleted', async () => {
    const { engine, repository } = makeSyncEngine();
    await engine.syncSourceItems('source-1', {
      mode: 'full',
      items: [
        new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h1' }),
        new DocumentItem({ externalId: 'b', name: 'b', path: '/b', contentHash: 'h2' }),
      ],
    });

    const summary = await engine.syncSourceItems('source-1', {
      mode: 'full',
      items: [new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h1' })],
    });

    expect(summary).toEqual({ created: 0, updated: 0, deleted: 1, moved: 0, unchanged: 1 });
    expect(await repository.listBySource('source-1')).toHaveLength(1);
  });

  test('publish đúng DomainEvent cho từng loại thay đổi', async () => {
    const { engine, eventBus } = makeSyncEngine();
    const received = [];
    eventBus.subscribe('*', (event) => received.push(event.eventType));

    await engine.syncSourceItems('source-1', {
      mode: 'full',
      items: [new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h1' })],
    });
    await engine.syncSourceItems('source-1', { mode: 'full', items: [] }); // 'a' bị xoá

    await new Promise((resolve) => setImmediate(resolve));
    expect(received).toEqual(['document.sync.created', 'document.sync.deleted']);
  });

  test('ghi sync_log cho mỗi thay đổi', async () => {
    const { engine, repository } = makeSyncEngine();
    await engine.syncSourceItems('source-1', {
      mode: 'full',
      items: [new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h1' })],
    });

    const log = await repository.getSyncLog('source-1');
    expect(log).toHaveLength(1);
    expect(log[0].changeType).toBe('created');
  });
});

describe('SyncEngine — delta apply', () => {
  test('item mới trong delta -> created', async () => {
    const { engine } = makeSyncEngine();
    const summary = await engine.syncSourceItems('source-1', {
      mode: 'delta',
      items: [new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h1' })],
    });
    expect(summary).toEqual({ created: 1, updated: 0, deleted: 0, moved: 0, unchanged: 0 });
  });

  test('item có removed=true -> deleted, KHÔNG cần biết toàn bộ danh sách còn lại', async () => {
    const { engine, repository } = makeSyncEngine();
    await engine.syncSourceItems('source-1', {
      mode: 'full',
      items: [
        new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h1' }),
        new DocumentItem({ externalId: 'b', name: 'b', path: '/b', contentHash: 'h2' }),
      ],
    });

    // Delta chỉ báo 'a' bị xoá — KHÔNG kèm 'b' trong danh sách (khác hẳn full-scan).
    const summary = await engine.syncSourceItems('source-1', {
      mode: 'delta',
      items: [new DocumentItem({ externalId: 'a', name: '(removed)', path: '(removed)', removed: true })],
    });

    expect(summary).toEqual({ created: 0, updated: 0, deleted: 1, moved: 0, unchanged: 0 });
    const remaining = await repository.listBySource('source-1');
    expect(remaining).toHaveLength(1);
    expect(remaining[0].externalId).toBe('b'); // 'b' KHÔNG bị xoá dù không có trong delta items
  });

  test('item đã tồn tại với contentHash đổi trong delta -> updated', async () => {
    const { engine } = makeSyncEngine();
    await engine.syncSourceItems('source-1', {
      mode: 'full',
      items: [new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h1' })],
    });

    const summary = await engine.syncSourceItems('source-1', {
      mode: 'delta',
      items: [new DocumentItem({ externalId: 'a', name: 'a', path: '/a', contentHash: 'h2' })],
    });

    expect(summary).toEqual({ created: 0, updated: 1, deleted: 0, moved: 0, unchanged: 0 });
  });
});

describe('SyncEngine — validation', () => {
  test('ném TypeError nếu thiếu sourceId', async () => {
    const { engine } = makeSyncEngine();
    await expect(engine.syncSourceItems(null, { mode: 'full', items: [] })).rejects.toThrow(TypeError);
  });

  test('ném TypeError nếu scanResult.items không phải mảng', async () => {
    const { engine } = makeSyncEngine();
    await expect(engine.syncSourceItems('source-1', { mode: 'full' })).rejects.toThrow(TypeError);
  });

  test('ném TypeError nếu mode không hợp lệ', async () => {
    const { engine } = makeSyncEngine();
    await expect(engine.syncSourceItems('source-1', { mode: 'khong-hop-le', items: [] })).rejects.toThrow(
      /mode không hợp lệ/
    );
  });
});

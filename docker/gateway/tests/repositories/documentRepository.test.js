'use strict';

const { InMemoryDocumentRepository } = require('../../repositories/documentRepository');
const { DocumentItem } = require('../../domain/DocumentItem');

describe('InMemoryDocumentRepository', () => {
  test('upsert + listBySource trả đúng item đã lưu', async () => {
    const repo = new InMemoryDocumentRepository();
    const item = new DocumentItem({ externalId: 'a', name: 'a.txt', path: '/a.txt' });

    await repo.upsert('source-1', item);
    const list = await repo.listBySource('source-1');

    expect(list).toHaveLength(1);
    expect(list[0].externalId).toBe('a');
  });

  test('listBySource trả mảng rỗng nếu source chưa từng sync', async () => {
    const repo = new InMemoryDocumentRepository();
    expect(await repo.listBySource('chua-ton-tai')).toEqual([]);
  });

  test('remove xoá đúng item theo externalId', async () => {
    const repo = new InMemoryDocumentRepository();
    await repo.upsert('source-1', new DocumentItem({ externalId: 'a', name: 'a', path: '/a' }));
    await repo.upsert('source-1', new DocumentItem({ externalId: 'b', name: 'b', path: '/b' }));

    await repo.remove('source-1', 'a');
    const list = await repo.listBySource('source-1');

    expect(list).toHaveLength(1);
    expect(list[0].externalId).toBe('b');
  });

  test('remove item không tồn tại không ném lỗi', async () => {
    const repo = new InMemoryDocumentRepository();
    await expect(repo.remove('source-khong-ton-tai', 'x')).resolves.toBeUndefined();
  });

  test('appendSyncLog + getSyncLog lưu đúng thứ tự', async () => {
    const repo = new InMemoryDocumentRepository();
    await repo.appendSyncLog('source-1', { changeType: 'created', externalId: 'a', occurredAt: '2026-01-01' });
    await repo.appendSyncLog('source-1', { changeType: 'updated', externalId: 'a', occurredAt: '2026-01-02' });

    const log = await repo.getSyncLog('source-1');
    expect(log).toHaveLength(2);
    expect(log[0].changeType).toBe('created');
    expect(log[1].changeType).toBe('updated');
  });

  test('dữ liệu giữa các source khác nhau độc lập, không lẫn nhau', async () => {
    const repo = new InMemoryDocumentRepository();
    await repo.upsert('source-1', new DocumentItem({ externalId: 'a', name: 'a', path: '/a' }));
    await repo.upsert('source-2', new DocumentItem({ externalId: 'b', name: 'b', path: '/b' }));

    expect(await repo.listBySource('source-1')).toHaveLength(1);
    expect(await repo.listBySource('source-2')).toHaveLength(1);
  });
});

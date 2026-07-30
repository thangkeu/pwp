'use strict';

const { DocumentItem } = require('../../domain/DocumentItem');

describe('DocumentItem', () => {
  test('tạo item hợp lệ với đầy đủ field', () => {
    const item = new DocumentItem({
      externalId: 'abc123',
      name: 'baogia.docx',
      path: '/Du an ABC/baogia.docx',
      mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      sizeBytes: 2048,
      contentHash: 'hash1',
      webUrl: 'https://drive.google.com/file/abc123',
    });

    expect(item.externalId).toBe('abc123');
    expect(item.sizeBytes).toBe(2048);
    expect(item.removed).toBe(false);
  });

  test('mimeType/sizeBytes/contentHash/webUrl có default hợp lý khi thiếu', () => {
    const item = new DocumentItem({ externalId: 'x', name: 'n', path: '/n' });
    expect(item.mimeType).toBe('application/octet-stream');
    expect(item.sizeBytes).toBe(0);
    expect(item.contentHash).toBeNull();
    expect(item.webUrl).toBeNull();
  });

  test('ném TypeError nếu thiếu externalId/name/path', () => {
    expect(() => new DocumentItem({ name: 'n', path: '/n' })).toThrow(TypeError);
    expect(() => new DocumentItem({ externalId: 'x', path: '/n' })).toThrow(TypeError);
    expect(() => new DocumentItem({ externalId: 'x', name: 'n' })).toThrow(TypeError);
  });

  test('removed=true dùng cho item bị xoá tại nguồn (delta connector)', () => {
    const item = new DocumentItem({ externalId: 'x', name: '(removed)', path: '(removed)', removed: true });
    expect(item.removed).toBe(true);
  });
});

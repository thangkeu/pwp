'use strict';

const { DomainEvent } = require('../../domain/DomainEvent');

describe('DomainEvent', () => {
  test('tạo event hợp lệ với eventId/occurredAt tự sinh', () => {
    const event = new DomainEvent('document.sync.completed', { docId: 1 }, { source: 'SyncEngine' });
    expect(event.eventId).toBeDefined();
    expect(event.eventType).toBe('document.sync.completed');
    expect(event.payload).toEqual({ docId: 1 });
    expect(event.source).toBe('SyncEngine');
    expect(new Date(event.occurredAt).toString()).not.toBe('Invalid Date');
  });

  test('payload mặc định là object rỗng nếu không truyền', () => {
    const event = new DomainEvent('system.health.checked', null);
    expect(event.payload).toEqual({});
  });

  test('ném TypeError nếu eventType rỗng', () => {
    expect(() => new DomainEvent('', {})).toThrow(TypeError);
    expect(() => new DomainEvent('   ', {})).toThrow(TypeError);
  });

  test('ném TypeError nếu eventType không phải chuỗi', () => {
    expect(() => new DomainEvent(123, {})).toThrow(TypeError);
  });

  test('ném TypeError nếu payload không phải object', () => {
    expect(() => new DomainEvent('a.b.c', 'not-an-object')).toThrow(TypeError);
  });

  test('toJSON() trả đủ field cần thiết để serialize', () => {
    const event = new DomainEvent('bom.item.approved', { bomId: 5 });
    const json = event.toJSON();
    expect(json).toMatchObject({
      eventId: event.eventId,
      eventType: 'bom.item.approved',
      payload: { bomId: 5 },
      occurredAt: event.occurredAt,
      source: 'unknown',
      correlationId: event.eventId
    });
  });

  test('fromJSON() khôi phục lại đúng eventId/occurredAt gốc (không sinh mới)', () => {
    const original = new DomainEvent('project.created', { projectId: 9 }, { source: 'ProjectService' });
    const serialized = JSON.stringify(original.toJSON());
    const restored = DomainEvent.fromJSON(serialized);

    expect(restored.eventId).toBe(original.eventId);
    expect(restored.occurredAt).toBe(original.occurredAt);
    expect(restored.eventType).toBe('project.created');
    expect(restored.payload).toEqual({ projectId: 9 });
    expect(restored.source).toBe('ProjectService');
  });

  test('fromJSON() chấp nhận object đã parse sẵn (không chỉ chuỗi)', () => {
    const original = new DomainEvent('x.y.z', { a: 1 });
    const restored = DomainEvent.fromJSON(original.toJSON());
    expect(restored.payload).toEqual({ a: 1 });
  });
});

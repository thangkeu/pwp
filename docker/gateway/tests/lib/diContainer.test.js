'use strict';

const { asValue } = require('awilix');
const { createDIContainer, registerService, buildEventBusTransport } = require('../../lib/diContainer');
const { InMemoryTransport, RedisStreamsTransport } = require('../../lib/eventBus');

describe('createDIContainer', () => {
  test('resolve được logger và eventBus mặc định (InMemoryTransport)', () => {
    const container = createDIContainer({});
    expect(container.resolve('logger')).toBeDefined();
    expect(container.resolve('eventBus')).toBeDefined();
    expect(container.resolve('eventBusTransport')).toBeInstanceOf(InMemoryTransport);
  });

  test('logger là singleton — resolve nhiều lần trả về cùng 1 instance', () => {
    const container = createDIContainer({});
    expect(container.resolve('logger')).toBe(container.resolve('logger'));
  });

  test('eventBus là singleton', () => {
    const container = createDIContainer({});
    expect(container.resolve('eventBus')).toBe(container.resolve('eventBus'));
  });
});

describe('buildEventBusTransport', () => {
  test('mặc định (không cấu hình) trả InMemoryTransport', () => {
    const transport = buildEventBusTransport({}, console);
    expect(transport).toBeInstanceOf(InMemoryTransport);
  });

  test('EVENT_BUS_DRIVER=redis trả RedisStreamsTransport', () => {
    const transport = buildEventBusTransport(
      { EVENT_BUS_DRIVER: 'redis', REDIS_URL: 'redis://localhost:6379' },
      console
    );
    expect(transport).toBeInstanceOf(RedisStreamsTransport);
  });

  test('EVENT_BUS_DRIVER=redis nhưng thiếu REDIS_URL thì ném lỗi rõ ràng (fail gracefully, không im lặng)', () => {
    expect(() => buildEventBusTransport({ EVENT_BUS_DRIVER: 'redis' }, console)).toThrow(
      /redisUrl/
    );
  });
});

describe('registerService', () => {
  test('đăng ký service mới thành công và resolve được', () => {
    const container = createDIContainer({});
    registerService(container, 'fakeService', asValue({ ping: () => 'pong' }));
    expect(container.resolve('fakeService').ping()).toBe('pong');
  });

  test('ném lỗi nếu đăng ký trùng tên service (chống ghi đè âm thầm)', () => {
    const container = createDIContainer({});
    registerService(container, 'fakeService', asValue({}));
    expect(() => registerService(container, 'fakeService', asValue({}))).toThrow(
      /đã được đăng ký/
    );
  });
});

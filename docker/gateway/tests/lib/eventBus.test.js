'use strict';

const { EventBus, InMemoryTransport } = require('../../lib/eventBus');
const { DomainEvent } = require('../../domain/DomainEvent');

/** Logger giả lập để assert log lỗi mà không in ra console khi chạy test. */
function makeSilentLogger() {
  return { error: jest.fn(), warn: jest.fn(), info: jest.fn() };
}

describe('EventBus (InMemoryTransport)', () => {
  test('subscribe nhận đúng event đã publish', async () => {
    const bus = new EventBus(new InMemoryTransport(), makeSilentLogger());
    const received = [];

    bus.subscribe('document.sync.completed', (event) => {
      received.push(event);
    });

    await bus.publish(new DomainEvent('document.sync.completed', { docId: 42 }));

    expect(received).toHaveLength(1);
    expect(received[0]).toBeInstanceOf(DomainEvent);
    expect(received[0].payload).toEqual({ docId: 42 });
  });

  test("subscribe('*') nhận mọi loại event", async () => {
    const bus = new EventBus(new InMemoryTransport(), makeSilentLogger());
    const received = [];
    bus.subscribe('*', (event) => received.push(event.eventType));

    await bus.publish(new DomainEvent('a.b.c', {}));
    await bus.publish(new DomainEvent('x.y.z', {}));

    expect(received).toEqual(['a.b.c', 'x.y.z']);
  });

  test('handler không quan tâm eventType khác thì không nhận được event', async () => {
    const bus = new EventBus(new InMemoryTransport(), makeSilentLogger());
    const received = [];
    bus.subscribe('bom.item.approved', (event) => received.push(event));

    await bus.publish(new DomainEvent('meeting.summary.created', {}));

    expect(received).toHaveLength(0);
  });

  test('unsubscribe() dừng nhận event tiếp theo', async () => {
    const bus = new EventBus(new InMemoryTransport(), makeSilentLogger());
    const received = [];
    const unsubscribe = bus.subscribe('a.b.c', (event) => received.push(event));

    await bus.publish(new DomainEvent('a.b.c', { n: 1 }));
    unsubscribe();
    await bus.publish(new DomainEvent('a.b.c', { n: 2 }));

    expect(received).toHaveLength(1);
    expect(received[0].payload).toEqual({ n: 1 });
  });

  test('publish() ném TypeError nếu không truyền instance DomainEvent', async () => {
    const bus = new EventBus(new InMemoryTransport(), makeSilentLogger());
    await expect(bus.publish({ eventType: 'fake' })).rejects.toThrow(TypeError);
  });

  test('subscribe() ném TypeError nếu handler không phải function', () => {
    const bus = new EventBus(new InMemoryTransport(), makeSilentLogger());
    expect(() => bus.subscribe('a.b.c', 'not-a-function')).toThrow(TypeError);
  });

  test('lỗi bên trong 1 handler không làm crash EventBus hay chặn handler khác', async () => {
    const logger = makeSilentLogger();
    const bus = new EventBus(new InMemoryTransport(), logger);
    const secondHandlerCalls = [];

    bus.subscribe('a.b.c', () => {
      throw new Error('handler lỗi cố ý');
    });
    bus.subscribe('a.b.c', (event) => secondHandlerCalls.push(event));

    await expect(bus.publish(new DomainEvent('a.b.c', {}))).resolves.toBeUndefined();

    // Chờ 1 tick để cả 2 handler async đều được gọi (EventEmitter gọi đồng bộ nhưng handler là async).
    await new Promise((resolve) => setImmediate(resolve));

    expect(secondHandlerCalls).toHaveLength(1);
    expect(logger.error).toHaveBeenCalledWith(
      expect.objectContaining({ eventType: 'a.b.c' }),
      expect.stringContaining('ném lỗi')
    );
  });

  test('close() không ném lỗi', async () => {
    const bus = new EventBus(new InMemoryTransport(), makeSilentLogger());
    await expect(bus.close()).resolves.toBeUndefined();
  });
});

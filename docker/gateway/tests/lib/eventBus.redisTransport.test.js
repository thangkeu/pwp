'use strict';

/**
 * Mock 'ioredis' TRƯỚC khi require eventBus.js, vì RedisStreamsTransport require('ioredis')
 * lazy bên trong constructor — jest.mock hoisted lên đầu file nên vẫn chặn đúng module thật.
 */
jest.mock('ioredis', () => {
  return jest.fn().mockImplementation(() => ({
    xadd: jest.fn().mockResolvedValue('1-0'),
    xread: jest.fn(),
    quit: jest.fn().mockResolvedValue('OK')
  }));
});

const { RedisStreamsTransport } = require('../../lib/eventBus');

function makeSilentLogger() {
  return { error: jest.fn(), warn: jest.fn(), info: jest.fn() };
}

describe('RedisStreamsTransport', () => {
  test('ném lỗi ngay khi thiếu redisUrl', () => {
    expect(() => new RedisStreamsTransport({})).toThrow(/redisUrl/);
  });

  test('publish() gọi XADD với stream key đúng prefix + JSON payload', async () => {
    const logger = makeSilentLogger();
    const transport = new RedisStreamsTransport({
      redisUrl: 'redis://localhost:6379',
      streamPrefix: 'pwp:events:',
      logger
    });

    await transport.publish('document.sync.completed', { docId: 1 });

    expect(transport._redis.xadd).toHaveBeenCalledWith(
      'pwp:events:document.sync.completed',
      '*',
      'data',
      JSON.stringify({ docId: 1 })
    );
  });

  test('publish() log lỗi và rethrow khi XADD thất bại (fail gracefully)', async () => {
    const logger = makeSilentLogger();
    const transport = new RedisStreamsTransport({ redisUrl: 'redis://x', logger });
    transport._redis.xadd.mockRejectedValueOnce(new Error('boom'));

    await expect(transport.publish('a.b.c', {})).rejects.toThrow('boom');
    expect(logger.error).toHaveBeenCalledWith(
      expect.objectContaining({ eventType: 'a.b.c' }),
      expect.stringContaining('publish thất bại')
    );
  });

  test('subscribe() đọc message từ XREAD và gọi handler với payload đã parse', async () => {
    const logger = makeSilentLogger();
    const transport = new RedisStreamsTransport({ redisUrl: 'redis://x', logger });
    const received = [];

    let callCount = 0;
    transport._redis.xread.mockImplementation(async () => {
      callCount += 1;
      if (callCount === 1) {
        return [
          [
            'pwp:events:a.b.c',
            [['1-0', ['data', JSON.stringify({ n: 1 })]]]
          ]
        ];
      }
      // Các lần gọi sau: dừng handler bằng cách unsubscribe từ bên ngoài test.
      await new Promise((resolve) => setTimeout(resolve, 5));
      return null;
    });

    const unsubscribe = transport.subscribe('a.b.c', (payload) => received.push(payload));

    // Chờ vòng lặp async trong subscribe() chạy ít nhất 1 lần.
    await new Promise((resolve) => setTimeout(resolve, 20));
    unsubscribe();

    expect(received).toEqual([{ n: 1 }]);
  });

  test('subscribe() không crash khi XREAD ném lỗi, log lỗi rồi thử lại', async () => {
    const logger = makeSilentLogger();
    const transport = new RedisStreamsTransport({ redisUrl: 'redis://x', logger });
    transport._redis.xread.mockRejectedValue(new Error('network lỗi'));

    const unsubscribe = transport.subscribe('a.b.c', jest.fn());
    await new Promise((resolve) => setTimeout(resolve, 20));
    unsubscribe();

    expect(logger.error).toHaveBeenCalledWith(
      expect.objectContaining({ eventType: 'a.b.c' }),
      expect.stringContaining('lỗi khi đọc stream')
    );
  });

  test('close() gọi quit() trên redis client và dừng mọi consumer', async () => {
    const transport = new RedisStreamsTransport({ redisUrl: 'redis://x', logger: makeSilentLogger() });
    const unsubscribeSpy = jest.fn();
    transport._consumers.push(unsubscribeSpy);

    await transport.close();

    expect(unsubscribeSpy).toHaveBeenCalled();
    expect(transport._redis.quit).toHaveBeenCalled();
  });
});

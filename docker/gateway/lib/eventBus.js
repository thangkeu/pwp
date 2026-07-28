'use strict';

const { EventEmitter } = require('events');
const { DomainEvent } = require('../domain/DomainEvent');

/**
 * InMemoryTransport — transport mặc định, dùng cho Sprint 0.3, dev local và unit test.
 * Không cần Redis chạy sẵn; mọi publish/subscribe diễn ra trong cùng 1 process.
 * KHÔNG dùng cho production nhiều instance Gateway (event sẽ không được chia sẻ giữa các process).
 */
class InMemoryTransport {
  constructor() {
    this._emitter = new EventEmitter();
    this._emitter.setMaxListeners(0);
  }

  /**
   * @param {string} eventType
   * @param {Object} serializedEvent - kết quả DomainEvent.toJSON()
   * @returns {Promise<void>}
   */
  async publish(eventType, serializedEvent) {
    this._emitter.emit(eventType, serializedEvent);
    this._emitter.emit('*', serializedEvent);
  }

  /**
   * @param {string} eventType - '*' để subscribe mọi event
   * @param {(serializedEvent: Object) => (void|Promise<void>)} handler
   * @returns {() => void} unsubscribe function
   */
  subscribe(eventType, handler) {
    this._emitter.on(eventType, handler);
    return () => this._emitter.off(eventType, handler);
  }

  async close() {
    this._emitter.removeAllListeners();
  }
}

/**
 * RedisStreamsTransport — transport production, dùng Redis Streams (XADD/XREAD) để
 * chia sẻ event giữa nhiều instance Gateway/AI services.
 * Chỉ khởi tạo kết nối khi thực sự dùng (lazy), tránh Sprint 0.3 bắt buộc phải có Redis chạy
 * để chạy được unit test (InMemoryTransport đã đủ cho test).
 */
class RedisStreamsTransport {
  /**
   * @param {Object} options
   * @param {string} options.redisUrl
   * @param {string} [options.streamPrefix='pwp:events:']
   * @param {import('pino').Logger} [options.logger]
   */
  constructor({ redisUrl, streamPrefix = 'pwp:events:', logger = console }) {
    if (!redisUrl) {
      throw new Error('RedisStreamsTransport yêu cầu redisUrl');
    }
    // require ioredis lazy để lib/eventBus.js không bắt buộc cài ioredis khi chỉ chạy test
    // với InMemoryTransport (giảm phụ thuộc cứng, đúng nguyên tắc Dependency Inversion).
    const Redis = require('ioredis');
    this._redis = new Redis(redisUrl, { lazyConnect: true });
    this._streamPrefix = streamPrefix;
    this._logger = logger;
    this._consumers = [];
  }

  _streamKey(eventType) {
    return `${this._streamPrefix}${eventType}`;
  }

  /**
   * @param {string} eventType
   * @param {Object} serializedEvent
   * @returns {Promise<void>}
   * @throws {Error} Khi Redis publish thất bại (Fail gracefully — caller phải xử lý/log)
   */
  async publish(eventType, serializedEvent) {
    try {
      await this._redis.xadd(
        this._streamKey(eventType),
        '*',
        'data',
        JSON.stringify(serializedEvent)
      );
    } catch (err) {
      this._logger.error({ err, eventType }, 'RedisStreamsTransport.publish thất bại');
      throw err;
    }
  }

  /**
   * @param {string} eventType
   * @param {(serializedEvent: Object) => (void|Promise<void>)} handler
   * @returns {() => void} unsubscribe function (dừng polling loop)
   */
  subscribe(eventType, handler) {
    let stopped = false;
    const streamKey = this._streamKey(eventType);

    (async () => {
      let lastId = '$'; // chỉ đọc event mới kể từ lúc subscribe
      while (!stopped) {
        try {
          const results = await this._redis.xread(
            'BLOCK', 5000, 'STREAMS', streamKey, lastId
          );
          if (!results) continue;
          for (const [, messages] of results) {
            for (const [id, fields] of messages) {
              lastId = id;
              const raw = fields[1]; // fields = ['data', '<json>']
              await handler(JSON.parse(raw));
            }
          }
        } catch (err) {
          this._logger.error({ err, eventType }, 'RedisStreamsTransport.subscribe lỗi khi đọc stream');
          // Fail gracefully: không throw ra ngoài loop, chờ 1s rồi thử lại thay vì "chết" consumer.
          await new Promise((resolve) => setTimeout(resolve, 1000));
        }
      }
    })();

    const unsubscribe = () => { stopped = true; };
    this._consumers.push(unsubscribe);
    return unsubscribe;
  }

  async close() {
    this._consumers.forEach((stop) => stop());
    await this._redis.quit();
  }
}

/**
 * EventBus — API duy nhất mà mọi module trong Gateway dùng để publish/subscribe DomainEvent.
 * Module nghiệp vụ KHÔNG được biết đang dùng InMemoryTransport hay RedisStreamsTransport
 * (Liskov Substitution — 2 transport cùng implement publish()/subscribe()/close()).
 */
class EventBus {
  /**
   * @param {{publish: Function, subscribe: Function, close: Function}} transport
   * @param {import('pino').Logger} [logger=console]
   */
  constructor(transport, logger = console) {
    this._transport = transport;
    this._logger = logger;
  }

  /**
   * Publish 1 DomainEvent.
   * @param {DomainEvent} event
   * @returns {Promise<void>}
   * @throws {TypeError} Khi event không phải instance DomainEvent
   */
  async publish(event) {
    if (!(event instanceof DomainEvent)) {
      throw new TypeError('EventBus.publish yêu cầu 1 instance DomainEvent');
    }
    try {
      await this._transport.publish(event.eventType, event.toJSON());
    } catch (err) {
      // Fail gracefully (Nguyên tắc 8, INSTRUCTIONS.md 1.5): log rõ ràng, không nuốt lỗi im lặng,
      // nhưng cũng không để 1 lỗi publish event làm crash toàn bộ request nghiệp vụ đang xử lý.
      this._logger.error({ err, eventType: event.eventType }, 'EventBus.publish thất bại');
      throw err;
    }
  }

  /**
   * Đăng ký handler cho 1 loại event.
   * @param {string} eventType - '*' để nhận mọi event (dùng cho audit/logging chung)
   * @param {(event: DomainEvent) => (void|Promise<void>)} handler
   * @returns {() => void} Hàm huỷ đăng ký
   */
  subscribe(eventType, handler) {
    if (typeof handler !== 'function') {
      throw new TypeError('EventBus.subscribe yêu cầu handler là function');
    }
    return this._transport.subscribe(eventType, async (serialized) => {
      try {
        await handler(DomainEvent.fromJSON(serialized));
      } catch (err) {
        this._logger.error(
          { err, eventType },
          'EventBus subscriber handler ném lỗi — event không được retry tự động'
        );
      }
    });
  }

  async close() {
    await this._transport.close();
  }
}

module.exports = { EventBus, InMemoryTransport, RedisStreamsTransport };

'use strict';

const { createContainer, asValue, asFunction, InjectionMode, Lifetime } = require('awilix');
const { createLogger } = require('./logger');
const { EventBus, InMemoryTransport, RedisStreamsTransport } = require('./eventBus');

/**
 * Xây dựng transport cho Event Bus dựa trên cấu hình môi trường.
 * Mặc định dùng InMemoryTransport (không cần Redis) — phù hợp Sprint 0.3, dev, test.
 * Đặt EVENT_BUS_DRIVER=redis + REDIS_URL để dùng RedisStreamsTransport ở production
 * (đúng Nguyên tắc 3 Config-driven — không hard-code driver).
 *
 * @param {NodeJS.ProcessEnv} env
 * @param {import('pino').Logger} logger
 * @returns {{publish: Function, subscribe: Function, close: Function}}
 */
function buildEventBusTransport(env, logger) {
  if (env.EVENT_BUS_DRIVER === 'redis') {
    return new RedisStreamsTransport({ redisUrl: env.REDIS_URL, logger });
  }
  return new InMemoryTransport();
}

/**
 * Tạo DI container gốc cho toàn bộ Gateway.
 *
 * Quy ước đăng ký:
 *   - Cross-cutting singleton (logger, eventBus, config) đăng ký ở đây.
 *   - Mỗi `services/*.js` mới tự đăng ký chính nó vào container này qua `registerService()`
 *     thay vì được import cứng ở index.js (Nguyên tắc 2 Module Registry, INSTRUCTIONS.md 1.5).
 *
 * @param {NodeJS.ProcessEnv} [env=process.env]
 * @returns {import('awilix').AwilixContainer}
 */
function createDIContainer(env = process.env) {
  const container = createContainer({ injectionMode: InjectionMode.PROXY });

  const appLogger = createLogger('application');
  const eventBusTransport = buildEventBusTransport(env, appLogger);

  container.register({
    env: asValue(env),
    logger: asFunction(() => appLogger).setLifetime(Lifetime.SINGLETON),
    eventBusTransport: asValue(eventBusTransport),
    eventBus: asFunction(
      ({ eventBusTransport: transport, logger }) => new EventBus(transport, logger)
    ).setLifetime(Lifetime.SINGLETON)
  });

  return container;
}

/**
 * Helper để 1 module service tự đăng ký vào container theo Module Registry Pattern.
 * Ví dụ dùng trong `services/documentService.js`:
 *   const { registerService } = require('../lib/diContainer');
 *   registerService(container, 'documentService', asFunction(makeDocumentService));
 *
 * @param {import('awilix').AwilixContainer} container
 * @param {string} name
 * @param {import('awilix').Resolver<any>} resolver
 * @throws {Error} Khi tên service đã được đăng ký (tránh ghi đè âm thầm)
 */
function registerService(container, name, resolver) {
  if (container.hasRegistration(name)) {
    throw new Error(`Service "${name}" đã được đăng ký — không cho phép ghi đè âm thầm.`);
  }
  container.register({ [name]: resolver });
}

module.exports = { createDIContainer, registerService, buildEventBusTransport };

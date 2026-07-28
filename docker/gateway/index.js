'use strict';

const express = require('express');
const { createDIContainer } = require('./lib/diContainer');
const { healthRouter } = require('./routes/health');

/**
 * Khởi tạo Express app + DI container. Tách khỏi app.listen() để unit/integration test
 * (supertest) dùng lại được `buildApp()` mà không cần mở port thật.
 *
 * @param {NodeJS.ProcessEnv} [env=process.env]
 * @returns {{ app: import('express').Express, container: import('awilix').AwilixContainer }}
 */
function buildApp(env = process.env) {
  const container = createDIContainer(env);
  const logger = container.resolve('logger');

  const app = express();
  app.use(express.json());

  // Auto-mount route: mỗi router mới trong routes/ đăng ký tại đây bằng 1 dòng, không sửa file
  // lõi khác (đúng Extensibility Contract, INSTRUCTIONS.md 2.7 mục 3).
  app.use('/api', healthRouter(container));

  app.use((err, req, res, _next) => {
    logger.error({ err, path: req.path }, 'Unhandled error ở Gateway');
    res.status(500).json({ error: 'internal_server_error' });
  });

  return { app, container };
}

/* istanbul ignore next -- chỉ chạy khi start thật, không chạy trong test */
if (require.main === module) {
  const { app, container } = buildApp();
  const port = process.env.PORT || 3000;
  app.listen(port, () => {
    container.resolve('logger').info({ port }, 'PWP Gateway đã khởi động');
  });
}

module.exports = { buildApp };

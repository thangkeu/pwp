'use strict';

const { Router } = require('express');
const { DomainEvent } = require('../domain/DomainEvent');

/**
 * Route Interface Adapter cho GET /api/health (INSTRUCTIONS.md 8.7 Post-Deployment Verification).
 * Không chứa logic nghiệp vụ — chỉ gọi eventBus để phát 'system.health.checked' cho Monitoring.
 *
 * @param {import('awilix').AwilixContainer} container
 * @returns {import('express').Router}
 */
function healthRouter(container) {
  const router = Router();

  router.get('/health', async (req, res) => {
    const eventBus = container.resolve('eventBus');
    try {
      await eventBus.publish(
        new DomainEvent('system.health.checked', { at: new Date().toISOString() }, {
          source: 'HealthRoute'
        })
      );
    } catch (err) {
      // Fail gracefully: health check vẫn trả 'ok' cho vòng lặp chính dù publish event lỗi,
      // vì bản thân việc publish event không phải điều kiện xác định hệ thống "khoẻ".
      container.resolve('logger').warn({ err }, 'Không publish được health event, bỏ qua');
    }
    res.json({ status: 'ok', service: 'pwp-gateway', version: process.env.npm_package_version });
  });

  return router;
}

module.exports = { healthRouter };

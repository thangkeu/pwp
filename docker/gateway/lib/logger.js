'use strict';

const pino = require('pino');

/**
 * Tạo 1 pino logger con, gắn field `logChannel` để phân biệt loại log khi query trên Loki
 * (Master Instructions: tách Application/Audit/Security/System/AI Usage Log).
 *
 * @param {'application'|'audit'|'security'|'system'|'ai_usage'} channel
 * @param {Object} [bindings] - Context bổ sung (vd: { module: 'EventBus' })
 * @returns {import('pino').Logger}
 */
function createLogger(channel, bindings = {}) {
  const base = pino({
    level: process.env.LOG_LEVEL || 'info',
    formatters: {
      level(label) {
        return { level: label };
      }
    },
    timestamp: pino.stdTimeFunctions.isoTime
  });
  return base.child({ logChannel: channel, ...bindings });
}

module.exports = { createLogger };

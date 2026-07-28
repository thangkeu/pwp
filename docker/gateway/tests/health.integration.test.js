'use strict';

const request = require('supertest');
const { buildApp } = require('../index');

describe('GET /api/health (integration)', () => {
  test('trả 200 và status ok', async () => {
    const { app } = buildApp({});
    const res = await request(app).get('/api/health');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({ status: 'ok', service: 'pwp-gateway' });
  });

  test('publish sự kiện system.health.checked lên EventBus khi được gọi', async () => {
    const { app, container } = buildApp({});
    const received = [];
    container.resolve('eventBus').subscribe('system.health.checked', (event) => {
      received.push(event);
    });

    await request(app).get('/api/health');
    await new Promise((resolve) => setImmediate(resolve));

    expect(received).toHaveLength(1);
    expect(received[0].source).toBe('HealthRoute');
  });
});

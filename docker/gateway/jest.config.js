/**
 * Jest config chuẩn cho PWP Gateway.
 * Theo INSTRUCTIONS.md Phần VII 7.5: bắt buộc unit test cho lib/ và services/
 * từ Sprint 3+ (nay là Sprint 1.x) trở đi; Sprint 0.3 thiết lập khung để các
 * Sprint sau kế thừa mà không phải cấu hình lại.
 */
module.exports = {
  testEnvironment: 'node',
  testMatch: ['**/tests/**/*.test.js'],
  collectCoverageFrom: [
    'lib/**/*.js',
    'services/**/*.js',
    'domain/**/*.js',
    '!**/node_modules/**'
  ],
  coverageThreshold: {
    // Ngưỡng tối thiểu cho code MỚI từ Sprint 0.3 trở đi.
    // Không áp cho toàn repo (nhiều file services/ chưa tồn tại ở Sprint 0.3).
    './lib/eventBus.js': { statements: 80, branches: 70, functions: 80, lines: 80 },
    './lib/diContainer.js': { statements: 80, branches: 70, functions: 80, lines: 80 }
  },
  verbose: true
};

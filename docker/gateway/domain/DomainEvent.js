'use strict';

const { randomUUID } = require('crypto');

/**
 * DomainEvent — cấu trúc chuẩn hoá cho MỌI sự kiện nghiệp vụ được publish qua Event Bus.
 *
 * Nguyên tắc (Master Instructions "Event Driven Design"):
 *   - Module không gọi trực tiếp lẫn nhau để thông báo thay đổi trạng thái; thay vào đó publish
 *     1 DomainEvent lên Event Bus, module khác tự subscribe nếu quan tâm.
 *   - `eventType` đặt tên theo dạng "<boundedContext>.<entity>.<action>",
 *     ví dụ: "document.sync.completed", "bom.item.approved".
 *
 * @typedef {Object} DomainEventPayload
 */
class DomainEvent {
  /**
   * @param {string} eventType - Tên sự kiện, dạng "<context>.<entity>.<action>"
   * @param {Object} payload - Dữ liệu nghiệp vụ đi kèm sự kiện (không chứa secret/token)
   * @param {Object} [options]
   * @param {string} [options.source] - Tên module phát sinh sự kiện (vd: "DocumentService")
   * @param {string} [options.correlationId] - ID để nối các event liên quan trong 1 luồng nghiệp vụ
   * @throws {TypeError} Khi eventType không phải chuỗi non-empty hoặc payload không phải object
   */
  constructor(eventType, payload, options = {}) {
    if (typeof eventType !== 'string' || eventType.trim().length === 0) {
      throw new TypeError('DomainEvent.eventType phải là chuỗi không rỗng');
    }
    if (payload !== null && typeof payload !== 'object') {
      throw new TypeError('DomainEvent.payload phải là object (hoặc null)');
    }

    this.eventId = randomUUID();
    this.eventType = eventType;
    this.payload = payload || {};
    this.occurredAt = new Date().toISOString();
    this.source = options.source || 'unknown';
    this.correlationId = options.correlationId || this.eventId;
  }

  /** @returns {Object} Dạng thuần JSON để serialize gửi qua Redis Streams / log */
  toJSON() {
    return {
      eventId: this.eventId,
      eventType: this.eventType,
      payload: this.payload,
      occurredAt: this.occurredAt,
      source: this.source,
      correlationId: this.correlationId
    };
  }

  /**
   * @param {string} raw - Chuỗi JSON đã serialize bằng toJSON()
   * @returns {DomainEvent}
   * @throws {SyntaxError} Khi raw không phải JSON hợp lệ
   */
  static fromJSON(raw) {
    const data = typeof raw === 'string' ? JSON.parse(raw) : raw;
    const event = new DomainEvent(data.eventType, data.payload, {
      source: data.source,
      correlationId: data.correlationId
    });
    // Giữ nguyên eventId/occurredAt gốc thay vì sinh mới, để không mất tính toàn vẹn khi replay.
    event.eventId = data.eventId;
    event.occurredAt = data.occurredAt;
    return event;
  }
}

module.exports = { DomainEvent };

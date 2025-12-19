const {
  getCurrentUTC,
  isValidISO8601,
  isStartBeforeEnd,
  isStartInFuture,
  doTimeRangesOverlap,
  validateTimeRange
} = require('../../src/utils/timeUtils');

describe('Time Utils', () => {
  describe('getCurrentUTC', () => {
    it('should return current time in ISO 8601 UTC format', () => {
      const result = getCurrentUTC();
      expect(isValidISO8601(result)).toBe(true);
      expect(result.endsWith('Z')).toBe(true);
    });
  });

  describe('isValidISO8601', () => {
    it('should validate correct ISO 8601 UTC strings', () => {
      expect(isValidISO8601('2024-01-15T10:00:00.000Z')).toBe(true);
      expect(isValidISO8601('2024-12-31T23:59:59.999Z')).toBe(true);
    });

    it('should reject non-ISO 8601 strings', () => {
      expect(isValidISO8601('2024-01-15 10:00:00')).toBe(false);
      expect(isValidISO8601('2024-01-15T10:00:00')).toBe(false);
      expect(isValidISO8601('invalid')).toBe(false);
      expect(isValidISO8601('')).toBe(false);
    });

    it('should reject non-string values', () => {
      expect(isValidISO8601(null)).toBe(false);
      expect(isValidISO8601(undefined)).toBe(false);
      expect(isValidISO8601(123)).toBe(false);
      expect(isValidISO8601({})).toBe(false);
    });
  });

  describe('isStartBeforeEnd', () => {
    it('should return true when start is before end', () => {
      const start = '2024-01-15T10:00:00.000Z';
      const end = '2024-01-15T11:00:00.000Z';
      expect(isStartBeforeEnd(start, end)).toBe(true);
    });

    it('should return false when start equals end', () => {
      const time = '2024-01-15T10:00:00.000Z';
      expect(isStartBeforeEnd(time, time)).toBe(false);
    });

    it('should return false when start is after end', () => {
      const start = '2024-01-15T11:00:00.000Z';
      const end = '2024-01-15T10:00:00.000Z';
      expect(isStartBeforeEnd(start, end)).toBe(false);
    });
  });

  describe('isStartInFuture', () => {
    it('should return true for future times', () => {
      const futureTime = new Date(Date.now() + 3600000).toISOString();
      expect(isStartInFuture(futureTime)).toBe(true);
    });

    it('should return false for past times', () => {
      const pastTime = new Date(Date.now() - 3600000).toISOString();
      expect(isStartInFuture(pastTime)).toBe(false);
    });

    it('should return true for current time (edge case)', () => {
      const now = new Date().toISOString();
      expect(isStartInFuture(now)).toBe(true);
    });
  });

  describe('doTimeRangesOverlap', () => {
    it('should detect overlap when ranges intersect', () => {
      const startA = '2024-01-15T10:00:00.000Z';
      const endA = '2024-01-15T12:00:00.000Z';
      const startB = '2024-01-15T11:00:00.000Z';
      const endB = '2024-01-15T13:00:00.000Z';
      expect(doTimeRangesOverlap(startA, endA, startB, endB)).toBe(true);
    });

    it('should detect overlap when B is completely inside A', () => {
      const startA = '2024-01-15T10:00:00.000Z';
      const endA = '2024-01-15T14:00:00.000Z';
      const startB = '2024-01-15T11:00:00.000Z';
      const endB = '2024-01-15T13:00:00.000Z';
      expect(doTimeRangesOverlap(startA, endA, startB, endB)).toBe(true);
    });

    it('should detect overlap when A is completely inside B', () => {
      const startA = '2024-01-15T11:00:00.000Z';
      const endA = '2024-01-15T13:00:00.000Z';
      const startB = '2024-01-15T10:00:00.000Z';
      const endB = '2024-01-15T14:00:00.000Z';
      expect(doTimeRangesOverlap(startA, endA, startB, endB)).toBe(true);
    });

    it('should not detect overlap when ranges are adjacent (end of A = start of B)', () => {
      const startA = '2024-01-15T10:00:00.000Z';
      const endA = '2024-01-15T12:00:00.000Z';
      const startB = '2024-01-15T12:00:00.000Z';
      const endB = '2024-01-15T14:00:00.000Z';
      expect(doTimeRangesOverlap(startA, endA, startB, endB)).toBe(false);
    });

    it('should not detect overlap when ranges are separate', () => {
      const startA = '2024-01-15T10:00:00.000Z';
      const endA = '2024-01-15T12:00:00.000Z';
      const startB = '2024-01-15T13:00:00.000Z';
      const endB = '2024-01-15T15:00:00.000Z';
      expect(doTimeRangesOverlap(startA, endA, startB, endB)).toBe(false);
    });

    it('should follow strict rule: (startA < endB) AND (startB < endA)', () => {
      const startA = '2024-01-15T10:00:00.000Z';
      const endA = '2024-01-15T11:00:00.000Z';
      const startB = '2024-01-15T10:30:00.000Z';
      const endB = '2024-01-15T11:30:00.000Z';
      expect(doTimeRangesOverlap(startA, endA, startB, endB)).toBe(true);
    });
  });

  describe('validateTimeRange', () => {
    const futureStart = new Date(Date.now() + 3600000).toISOString();
    const futureEnd = new Date(Date.now() + 7200000).toISOString();

    it('should validate correct time range', () => {
      const result = validateTimeRange(futureStart, futureEnd);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should reject invalid start time format', () => {
      const result = validateTimeRange('invalid', futureEnd);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Start time must be valid ISO 8601 UTC format');
    });

    it('should reject invalid end time format', () => {
      const result = validateTimeRange(futureStart, 'invalid');
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('End time must be valid ISO 8601 UTC format');
    });

    it('should reject when start is not before end', () => {
      const result = validateTimeRange(futureEnd, futureStart);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Start time must be before end time');
    });

    it('should reject when start equals end', () => {
      const result = validateTimeRange(futureStart, futureStart);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Start time must be before end time');
    });

    it('should reject when start is in the past', () => {
      const pastStart = new Date(Date.now() - 3600000).toISOString();
      const pastEnd = new Date(Date.now() - 1800000).toISOString();
      const result = validateTimeRange(pastStart, pastEnd);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain('Start time must be in the future');
    });

    it('should return multiple errors when multiple validations fail', () => {
      const pastTime = new Date(Date.now() - 3600000).toISOString();
      const result = validateTimeRange(pastTime, pastTime);
      expect(result.valid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(1);
    });
  });
});

const {
  getCurrentUTC,
  isValidISO8601,
  isStartBeforeEnd,
  isStartInFuture,
  doTimeRangesOverlap,
  validateTimeRange,
} = require("../../src/utils/timeUtils");

describe("Time Utils", () => {
  describe("getCurrentUTC", () => {
    it("should return current time in ISO 8601 UTC format", () => {
      const result = getCurrentUTC();
      expect(isValidISO8601(result)).toBe(true);
      expect(result.endsWith("Z")).toBe(true);
    });
  });

  describe("isValidISO8601", () => {
    it("should validate ISO 8601 strings correctly", () => {
      // Valid strings
      expect(isValidISO8601("2024-01-15T10:00:00.000Z")).toBe(true);
      expect(isValidISO8601("2024-12-31T23:59:59.999Z")).toBe(true);
      // Invalid strings
      expect(isValidISO8601("2024-01-15 10:00:00")).toBe(false);
      expect(isValidISO8601("2024-01-15T10:00:00")).toBe(false);
      expect(isValidISO8601("invalid")).toBe(false);
      expect(isValidISO8601("")).toBe(false);
      // Non-string values
      expect(isValidISO8601(null)).toBe(false);
      expect(isValidISO8601(undefined)).toBe(false);
      expect(isValidISO8601(123)).toBe(false);
    });
  });

  describe("isStartBeforeEnd", () => {
    it("should correctly compare start and end times", () => {
      expect(isStartBeforeEnd("2024-01-15T10:00:00.000Z", "2024-01-15T11:00:00.000Z")).toBe(true);
      expect(isStartBeforeEnd("2024-01-15T10:00:00.000Z", "2024-01-15T10:00:00.000Z")).toBe(false);
      expect(isStartBeforeEnd("2024-01-15T11:00:00.000Z", "2024-01-15T10:00:00.000Z")).toBe(false);
    });
  });

  describe("isStartInFuture", () => {
    it("should correctly identify future and past times", () => {
      const futureTime = new Date(Date.now() + 3600000).toISOString();
      const pastTime = new Date(Date.now() - 3600000).toISOString();
      expect(isStartInFuture(futureTime)).toBe(true);
      expect(isStartInFuture(pastTime)).toBe(false);
    });
  });

  describe("doTimeRangesOverlap", () => {
    it("should detect overlapping and non-overlapping ranges", () => {
      // Overlapping ranges
      expect(doTimeRangesOverlap(
        "2024-01-15T10:00:00.000Z", "2024-01-15T12:00:00.000Z",
        "2024-01-15T11:00:00.000Z", "2024-01-15T13:00:00.000Z"
      )).toBe(true);
      
      // B inside A
      expect(doTimeRangesOverlap(
        "2024-01-15T10:00:00.000Z", "2024-01-15T14:00:00.000Z",
        "2024-01-15T11:00:00.000Z", "2024-01-15T13:00:00.000Z"
      )).toBe(true);
      
      // Adjacent (not overlapping)
      expect(doTimeRangesOverlap(
        "2024-01-15T10:00:00.000Z", "2024-01-15T12:00:00.000Z",
        "2024-01-15T12:00:00.000Z", "2024-01-15T14:00:00.000Z"
      )).toBe(false);
      
      // Separate ranges
      expect(doTimeRangesOverlap(
        "2024-01-15T10:00:00.000Z", "2024-01-15T12:00:00.000Z",
        "2024-01-15T13:00:00.000Z", "2024-01-15T15:00:00.000Z"
      )).toBe(false);
    });
  });

  describe("validateTimeRange", () => {
    const futureStart = new Date(Date.now() + 3600000).toISOString();
    const futureEnd = new Date(Date.now() + 7200000).toISOString();

    it("should validate correct time range", () => {
      const result = validateTimeRange(futureStart, futureEnd);
      expect(result.valid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it("should reject invalid time formats and ranges", () => {
      // Invalid start time format
      let result = validateTimeRange("invalid", futureEnd);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain("Start time must be valid ISO 8601 UTC format");

      // Invalid end time format
      result = validateTimeRange(futureStart, "invalid");
      expect(result.valid).toBe(false);
      expect(result.errors).toContain("End time must be valid ISO 8601 UTC format");

      // Start after end
      result = validateTimeRange(futureEnd, futureStart);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain("Start time must be before end time");

      // Past start time
      const pastStart = new Date(Date.now() - 3600000).toISOString();
      result = validateTimeRange(pastStart, futureEnd);
      expect(result.valid).toBe(false);
      expect(result.errors).toContain("Start time must be in the future");
    });
  });
});

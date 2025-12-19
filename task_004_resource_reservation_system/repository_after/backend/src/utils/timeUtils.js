/**
 * Time utility functions for reservation system.
 * All time operations use UTC to ensure consistency.
 */

/**
 * Get current server time in ISO 8601 UTC format
 */
function getCurrentUTC() {
  return new Date().toISOString();
}

/**
 * Check if a time string is valid ISO 8601 format
 */
function isValidISO8601(timeString) {
  if (typeof timeString !== 'string') {
    return false;
  }
  
  const date = new Date(timeString);
  return !isNaN(date.getTime()) && date.toISOString() === timeString;
}

/**
 * Check if start time is before end time
 */
function isStartBeforeEnd(startTime, endTime) {
  return new Date(startTime) < new Date(endTime);
}

/**
 * Check if start time is in the future (>= current time)
 */
function isStartInFuture(startTime) {
  return new Date(startTime) >= new Date();
}

/**
 * Check if two time ranges overlap using the strict rule:
 * Two ranges overlap if and only if: (startA < endB) AND (startB < endA)
 */
function doTimeRangesOverlap(startA, endA, startB, endB) {
  const startADate = new Date(startA);
  const endADate = new Date(endA);
  const startBDate = new Date(startB);
  const endBDate = new Date(endB);
  
  return (startADate < endBDate) && (startBDate < endADate);
}

/**
 * Validate time range according to system rules
 */
function validateTimeRange(startTime, endTime) {
  const errors = [];
  
  if (!isValidISO8601(startTime)) {
    errors.push('Start time must be valid ISO 8601 UTC format');
  }
  
  if (!isValidISO8601(endTime)) {
    errors.push('End time must be valid ISO 8601 UTC format');
  }
  
  if (errors.length > 0) {
    return { valid: false, errors };
  }
  
  if (!isStartBeforeEnd(startTime, endTime)) {
    errors.push('Start time must be before end time');
  }
  
  if (!isStartInFuture(startTime)) {
    errors.push('Start time must be in the future');
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

module.exports = {
  getCurrentUTC,
  isValidISO8601,
  isStartBeforeEnd,
  isStartInFuture,
  doTimeRangesOverlap,
  validateTimeRange
};

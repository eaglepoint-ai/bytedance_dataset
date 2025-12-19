const database = require('../database/db');
const { validateTimeRange, doTimeRangesOverlap } = require('../utils/timeUtils');

/**
 * Reservation state machine transitions
 */
const VALID_TRANSITIONS = {
  pending: ['approved', 'rejected'],
  approved: ['cancelled'],
  rejected: [],
  cancelled: [],
  blocked: []
};

/**
 * Check if state transition is valid
 */
function isValidTransition(currentStatus, newStatus) {
  return VALID_TRANSITIONS[currentStatus]?.includes(newStatus) || false;
}

/**
 * Check if resource is active
 */
async function isResourceActive(resourceId) {
  const resource = await database.get(
    'SELECT status FROM resources WHERE id = ?',
    [resourceId]
  );
  
  return resource && resource.status === 'active';
}

/**
 * Check for overlapping reservations with proper locking
 * CRITICAL: This must be called within a transaction with proper locking
 */
async function checkOverlap(resourceId, startTime, endTime, excludeReservationId = null) {
  let query = `
    SELECT id, start_time, end_time, status 
    FROM reservations 
    WHERE resource_id = ? 
      AND status IN ('approved', 'blocked')
  `;
  
  const params = [resourceId];
  
  if (excludeReservationId) {
    query += ' AND id != ?';
    params.push(excludeReservationId);
  }
  
  const existingReservations = await database.all(query, params);
  
  for (const reservation of existingReservations) {
    if (doTimeRangesOverlap(
      startTime, 
      endTime, 
      reservation.start_time, 
      reservation.end_time
    )) {
      return {
        hasOverlap: true,
        conflictingReservation: reservation
      };
    }
  }
  
  return { hasOverlap: false };
}

/**
 * Create a reservation request (user action)
 * Uses transaction with IMMEDIATE locking to prevent race conditions
 */
async function createReservation(resourceId, userId, startTime, endTime) {
  const timeValidation = validateTimeRange(startTime, endTime);
  
  if (!timeValidation.valid) {
    throw new Error(timeValidation.errors.join(', '));
  }
  
  try {
    await database.beginTransaction();
    
    const isActive = await isResourceActive(resourceId);
    if (!isActive) {
      await database.rollback();
      throw new Error('Resource is not active');
    }
    
    const overlapCheck = await checkOverlap(resourceId, startTime, endTime);
    if (overlapCheck.hasOverlap) {
      await database.rollback();
      throw new Error('Time slot conflicts with existing reservation');
    }
    
    const result = await database.run(
      `INSERT INTO reservations 
       (resource_id, user_id, start_time, end_time, status) 
       VALUES (?, ?, ?, ?, 'pending')`,
      [resourceId, userId, startTime, endTime]
    );
    
    await database.commit();
    
    return {
      id: result.lastID,
      resourceId,
      userId,
      startTime,
      endTime,
      status: 'pending'
    };
  } catch (error) {
    try {
      await database.rollback();
    } catch (rollbackError) {
      // Ignore rollback errors if transaction is already closed
    }
    throw error;
  }
}

/**
 * Approve a reservation (admin action)
 * Double-checks for conflicts before approval to handle race conditions
 */
async function approveReservation(reservationId, adminId) {
  try {
    await database.beginTransaction();
    
    const reservation = await database.get(
      'SELECT * FROM reservations WHERE id = ?',
      [reservationId]
    );
    
    if (!reservation) {
      await database.rollback();
      throw new Error('Reservation not found');
    }
    
    if (!isValidTransition(reservation.status, 'approved')) {
      await database.rollback();
      throw new Error(`Cannot approve reservation with status: ${reservation.status}`);
    }
    
    const overlapCheck = await checkOverlap(
      reservation.resource_id,
      reservation.start_time,
      reservation.end_time,
      reservationId
    );
    
    if (overlapCheck.hasOverlap) {
      await database.rollback();
      throw new Error('Cannot approve: time slot now conflicts with another reservation');
    }
    
    await database.run(
      `UPDATE reservations 
       SET status = 'approved', updated_at = datetime('now', 'utc') 
       WHERE id = ?`,
      [reservationId]
    );
    
    await database.commit();
    
    return { ...reservation, status: 'approved' };
  } catch (error) {
    try {
      await database.rollback();
    } catch (rollbackError) {
      // Ignore rollback errors if transaction is already closed
    }
    throw error;
  }
}

/**
 * Reject a reservation (admin action)
 */
async function rejectReservation(reservationId, adminId) {
  const reservation = await database.get(
    'SELECT * FROM reservations WHERE id = ?',
    [reservationId]
  );
  
  if (!reservation) {
    throw new Error('Reservation not found');
  }
  
  if (!isValidTransition(reservation.status, 'rejected')) {
    throw new Error(`Cannot reject reservation with status: ${reservation.status}`);
  }
  
  await database.run(
    `UPDATE reservations 
     SET status = 'rejected', updated_at = datetime('now', 'utc') 
     WHERE id = ?`,
    [reservationId]
  );
  
  return { ...reservation, status: 'rejected' };
}

/**
 * Cancel a reservation (admin or owner action)
 */
async function cancelReservation(reservationId, userId, isAdmin) {
  const reservation = await database.get(
    'SELECT * FROM reservations WHERE id = ?',
    [reservationId]
  );
  
  if (!reservation) {
    throw new Error('Reservation not found');
  }
  
  if (!isAdmin && reservation.user_id !== userId) {
    throw new Error('Cannot cancel another user\'s reservation');
  }
  
  if (!isValidTransition(reservation.status, 'cancelled')) {
    throw new Error(`Cannot cancel reservation with status: ${reservation.status}`);
  }
  
  await database.run(
    `UPDATE reservations 
     SET status = 'cancelled', updated_at = datetime('now', 'utc') 
     WHERE id = ?`,
    [reservationId]
  );
  
  return { ...reservation, status: 'cancelled' };
}

/**
 * Create a blocked time slot (admin action)
 */
async function createBlockedSlot(resourceId, startTime, endTime, adminId) {
  const timeValidation = validateTimeRange(startTime, endTime);
  
  if (!timeValidation.valid) {
    throw new Error(timeValidation.errors.join(', '));
  }
  
  try {
    await database.beginTransaction();
    
    const isActive = await isResourceActive(resourceId);
    if (!isActive) {
      await database.rollback();
      throw new Error('Resource is not active');
    }
    
    const overlapCheck = await checkOverlap(resourceId, startTime, endTime);
    if (overlapCheck.hasOverlap) {
      await database.rollback();
      throw new Error('Time slot conflicts with existing reservation');
    }
    
    const result = await database.run(
      `INSERT INTO reservations 
       (resource_id, user_id, start_time, end_time, status) 
       VALUES (?, NULL, ?, ?, 'blocked')`,
      [resourceId, startTime, endTime]
    );
    
    await database.commit();
    
    return {
      id: result.lastID,
      resourceId,
      userId: null,
      startTime,
      endTime,
      status: 'blocked'
    };
  } catch (error) {
    try {
      await database.rollback();
    } catch (rollbackError) {
      // Ignore rollback errors if transaction is already closed
    }
    throw error;
  }
}

/**
 * Get reservations with role-based filtering
 */
async function getReservations(userId, isAdmin) {
  if (isAdmin) {
    return database.all(`
      SELECT r.*, u.name as user_name, res.name as resource_name
      FROM reservations r
      LEFT JOIN users u ON r.user_id = u.id
      LEFT JOIN resources res ON r.resource_id = res.id
      ORDER BY r.start_time DESC
    `);
  } else {
    return database.all(
      `SELECT r.*, u.name as user_name, res.name as resource_name
       FROM reservations r
       LEFT JOIN users u ON r.user_id = u.id
       LEFT JOIN resources res ON r.resource_id = res.id
       WHERE r.user_id = ?
       ORDER BY r.start_time DESC`,
      [userId]
    );
  }
}

/**
 * Get reservation by ID with authorization check
 */
async function getReservationById(reservationId, userId, isAdmin) {
  const reservation = await database.get(
    `SELECT r.*, u.name as user_name, res.name as resource_name
     FROM reservations r
     LEFT JOIN users u ON r.user_id = u.id
     LEFT JOIN resources res ON r.resource_id = res.id
     WHERE r.id = ?`,
    [reservationId]
  );
  
  if (!reservation) {
    throw new Error('Reservation not found');
  }
  
  if (!isAdmin && reservation.user_id !== userId) {
    throw new Error('Access denied');
  }
  
  return reservation;
}

module.exports = {
  isValidTransition,
  createReservation,
  approveReservation,
  rejectReservation,
  cancelReservation,
  createBlockedSlot,
  getReservations,
  getReservationById,
  checkOverlap
};

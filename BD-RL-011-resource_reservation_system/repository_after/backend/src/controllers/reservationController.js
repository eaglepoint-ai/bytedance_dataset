const express = require('express');
const reservationService = require('../services/reservationService');
const { authenticate, adminOnly } = require('../middleware/auth');

const router = express.Router();

/**
 * GET /api/reservations
 * Get reservations (role-based filtering)
 */
router.get('/', authenticate, async (req, res) => {
  try {
    const reservations = await reservationService.getReservations(
      req.user.id,
      req.user.role === 'admin'
    );
    
    res.json({ reservations });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/reservations/:id
 * Get reservation by ID (with authorization check)
 */
router.get('/:id', authenticate, async (req, res) => {
  try {
    const reservation = await reservationService.getReservationById(
      req.params.id,
      req.user.id,
      req.user.role === 'admin'
    );
    
    res.json({ reservation });
  } catch (error) {
    if (error.message === 'Reservation not found') {
      return res.status(404).json({ error: error.message });
    }
    if (error.message === 'Access denied') {
      return res.status(403).json({ error: error.message });
    }
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/reservations
 * Create reservation request (user action)
 */
router.post('/', authenticate, async (req, res) => {
  try {
    const { resourceId, startTime, endTime } = req.body;
    
    if (!resourceId || !startTime || !endTime) {
      return res.status(400).json({ 
        error: 'Resource ID, start time, and end time are required' 
      });
    }
    
    const reservation = await reservationService.createReservation(
      resourceId,
      req.user.id,
      startTime,
      endTime
    );
    
    res.status(201).json({ reservation });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

/**
 * POST /api/reservations/:id/approve
 * Approve reservation (admin only)
 */
router.post('/:id/approve', authenticate, adminOnly, async (req, res) => {
  try {
    const reservation = await reservationService.approveReservation(
      req.params.id,
      req.user.id
    );
    
    res.json({ reservation });
  } catch (error) {
    if (error.message === 'Reservation not found') {
      return res.status(404).json({ error: error.message });
    }
    res.status(400).json({ error: error.message });
  }
});

/**
 * POST /api/reservations/:id/reject
 * Reject reservation (admin only)
 */
router.post('/:id/reject', authenticate, adminOnly, async (req, res) => {
  try {
    const reservation = await reservationService.rejectReservation(
      req.params.id,
      req.user.id
    );
    
    res.json({ reservation });
  } catch (error) {
    if (error.message === 'Reservation not found') {
      return res.status(404).json({ error: error.message });
    }
    res.status(400).json({ error: error.message });
  }
});

/**
 * POST /api/reservations/:id/cancel
 * Cancel reservation (admin or owner)
 */
router.post('/:id/cancel', authenticate, async (req, res) => {
  try {
    const reservation = await reservationService.cancelReservation(
      req.params.id,
      req.user.id,
      req.user.role === 'admin'
    );
    
    res.json({ reservation });
  } catch (error) {
    if (error.message === 'Reservation not found') {
      return res.status(404).json({ error: error.message });
    }
    if (error.message.includes('Cannot cancel')) {
      return res.status(403).json({ error: error.message });
    }
    res.status(400).json({ error: error.message });
  }
});

/**
 * POST /api/reservations/blocked
 * Create blocked time slot (admin only)
 */
router.post('/blocked', authenticate, adminOnly, async (req, res) => {
  try {
    const { resourceId, startTime, endTime } = req.body;
    
    if (!resourceId || !startTime || !endTime) {
      return res.status(400).json({ 
        error: 'Resource ID, start time, and end time are required' 
      });
    }
    
    const blockedSlot = await reservationService.createBlockedSlot(
      resourceId,
      startTime,
      endTime,
      req.user.id
    );
    
    res.status(201).json({ reservation: blockedSlot });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

module.exports = router;

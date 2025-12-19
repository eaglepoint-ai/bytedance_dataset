const express = require('express');
const resourceService = require('../services/resourceService');
const { authenticate, adminOnly } = require('../middleware/auth');

const router = express.Router();

/**
 * GET /api/resources
 * Get all resources (authenticated users)
 */
router.get('/', authenticate, async (req, res) => {
  try {
    const resources = req.user.role === 'admin' 
      ? await resourceService.getAllResources()
      : await resourceService.getActiveResources();
    
    res.json({ resources });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

/**
 * GET /api/resources/:id
 * Get resource by ID
 */
router.get('/:id', authenticate, async (req, res) => {
  try {
    const resource = await resourceService.getResourceById(req.params.id);
    res.json({ resource });
  } catch (error) {
    if (error.message === 'Resource not found') {
      return res.status(404).json({ error: error.message });
    }
    res.status(500).json({ error: error.message });
  }
});

/**
 * POST /api/resources
 * Create new resource (admin only)
 */
router.post('/', authenticate, adminOnly, async (req, res) => {
  try {
    const { name, type } = req.body;
    
    if (!name || !type) {
      return res.status(400).json({ error: 'Name and type are required' });
    }
    
    const resource = await resourceService.createResource(
      name,
      type,
      req.user.id
    );
    
    res.status(201).json({ resource });
  } catch (error) {
    res.status(400).json({ error: error.message });
  }
});

/**
 * PUT /api/resources/:id
 * Update resource (admin only)
 */
router.put('/:id', authenticate, adminOnly, async (req, res) => {
  try {
    const resource = await resourceService.updateResource(
      req.params.id,
      req.body,
      req.user.id
    );
    
    res.json({ resource });
  } catch (error) {
    if (error.message === 'Resource not found') {
      return res.status(404).json({ error: error.message });
    }
    res.status(400).json({ error: error.message });
  }
});

module.exports = router;

const database = require('../database/db');

/**
 * Create a new resource (admin only)
 */
async function createResource(name, type, createdBy) {
  const validTypes = ['room', 'vehicle', 'equipment'];
  
  if (!validTypes.includes(type)) {
    throw new Error('Invalid resource type');
  }
  
  const result = await database.run(
    'INSERT INTO resources (name, type, status, created_by) VALUES (?, ?, ?, ?)',
    [name, type, 'active', createdBy]
  );
  
  return {
    id: result.lastID,
    name,
    type,
    status: 'active',
    createdBy
  };
}

/**
 * Update resource (admin only)
 */
async function updateResource(id, updates, adminId) {
  const resource = await database.get(
    'SELECT * FROM resources WHERE id = ?',
    [id]
  );
  
  if (!resource) {
    throw new Error('Resource not found');
  }
  
  const allowedUpdates = ['name', 'type', 'status'];
  const updateFields = [];
  const updateValues = [];
  
  for (const [key, value] of Object.entries(updates)) {
    if (allowedUpdates.includes(key)) {
      if (key === 'type' && !['room', 'vehicle', 'equipment'].includes(value)) {
        throw new Error('Invalid resource type');
      }
      if (key === 'status' && !['active', 'inactive'].includes(value)) {
        throw new Error('Invalid resource status');
      }
      
      updateFields.push(`${key} = ?`);
      updateValues.push(value);
    }
  }
  
  if (updateFields.length === 0) {
    throw new Error('No valid fields to update');
  }
  
  updateValues.push(id);
  
  await database.run(
    `UPDATE resources SET ${updateFields.join(', ')} WHERE id = ?`,
    updateValues
  );
  
  return database.get('SELECT * FROM resources WHERE id = ?', [id]);
}

/**
 * Get all resources
 */
async function getAllResources() {
  return database.all(`
    SELECT r.*, u.name as created_by_name
    FROM resources r
    LEFT JOIN users u ON r.created_by = u.id
    ORDER BY r.created_at DESC
  `);
}

/**
 * Get resource by ID
 */
async function getResourceById(id) {
  const resource = await database.get(
    `SELECT r.*, u.name as created_by_name
     FROM resources r
     LEFT JOIN users u ON r.created_by = u.id
     WHERE r.id = ?`,
    [id]
  );
  
  if (!resource) {
    throw new Error('Resource not found');
  }
  
  return resource;
}

/**
 * Get active resources only
 */
async function getActiveResources() {
  return database.all(`
    SELECT r.*, u.name as created_by_name
    FROM resources r
    LEFT JOIN users u ON r.created_by = u.id
    WHERE r.status = 'active'
    ORDER BY r.name ASC
  `);
}

module.exports = {
  createResource,
  updateResource,
  getAllResources,
  getResourceById,
  getActiveResources
};

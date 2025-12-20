const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const database = require('../database/db');

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';
const JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '24h';

/**
 * Hash password using bcrypt
 */
async function hashPassword(password) {
  return bcrypt.hash(password, 10);
}

/**
 * Compare password with hash
 */
async function comparePassword(password, hash) {
  return bcrypt.compare(password, hash);
}

/**
 * Generate JWT token for user
 */
function generateToken(user) {
  return jwt.sign(
    { 
      id: user.id, 
      email: user.email, 
      role: user.role 
    },
    JWT_SECRET,
    { expiresIn: JWT_EXPIRES_IN }
  );
}

/**
 * Verify JWT token
 */
function verifyToken(token) {
  try {
    return jwt.verify(token, JWT_SECRET);
  } catch (error) {
    return null;
  }
}

/**
 * Register a new user
 */
async function register(name, email, password, role = 'user') {
  if (!['admin', 'user'].includes(role)) {
    throw new Error('Invalid role');
  }

  const existingUser = await database.get(
    'SELECT id FROM users WHERE email = ?',
    [email]
  );

  if (existingUser) {
    throw new Error('Email already registered');
  }

  const hashedPassword = await hashPassword(password);
  
  const result = await database.run(
    'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
    [name, email, hashedPassword, role]
  );

  return {
    id: result.lastID,
    name,
    email,
    role
  };
}

/**
 * Login user and return token
 */
async function login(email, password) {
  const user = await database.get(
    'SELECT id, name, email, password, role FROM users WHERE email = ?',
    [email]
  );

  if (!user) {
    throw new Error('Invalid credentials');
  }

  const isValidPassword = await comparePassword(password, user.password);

  if (!isValidPassword) {
    throw new Error('Invalid credentials');
  }

  const token = generateToken(user);

  return {
    token,
    user: {
      id: user.id,
      name: user.name,
      email: user.email,
      role: user.role
    }
  };
}

/**
 * Get user by ID
 */
async function getUserById(id) {
  return database.get(
    'SELECT id, name, email, role FROM users WHERE id = ?',
    [id]
  );
}

module.exports = {
  hashPassword,
  comparePassword,
  generateToken,
  verifyToken,
  register,
  login,
  getUserById
};

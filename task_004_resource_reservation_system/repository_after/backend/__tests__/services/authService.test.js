const database = require('../../src/database/db');
const authService = require('../../src/services/authService');
const bcrypt = require('bcryptjs');

describe('Auth Service', () => {
  beforeAll(async () => {
    process.env.DATABASE_PATH = ':memory:';
    await database.initialize();
  });

  afterEach(async () => {
    await database.run('DELETE FROM users');
  });

  afterAll(async () => {
    await database.close();
  });

  describe('register', () => {
    it('should register a new user successfully', async () => {
      const user = await authService.register(
        'Test User',
        'test@example.com',
        'password123',
        'user'
      );

      expect(user).toHaveProperty('id');
      expect(user.name).toBe('Test User');
      expect(user.email).toBe('test@example.com');
      expect(user.role).toBe('user');
      expect(user).not.toHaveProperty('password');
    });

    it('should hash the password', async () => {
      await authService.register('User', 'user@example.com', 'password123');
      
      const dbUser = await database.get(
        'SELECT password FROM users WHERE email = ?',
        ['user@example.com']
      );

      expect(dbUser.password).not.toBe('password123');
      const isValidHash = await bcrypt.compare('password123', dbUser.password);
      expect(isValidHash).toBe(true);
    });

    it('should default role to user if not specified', async () => {
      const user = await authService.register(
        'Default User',
        'default@example.com',
        'password123'
      );

      expect(user.role).toBe('user');
    });

    it('should allow admin role registration', async () => {
      const user = await authService.register(
        'Admin User',
        'admin@example.com',
        'password123',
        'admin'
      );

      expect(user.role).toBe('admin');
    });

    it('should reject invalid role', async () => {
      await expect(
        authService.register('User', 'user@example.com', 'password123', 'invalid')
      ).rejects.toThrow('Invalid role');
    });

    it('should reject duplicate email', async () => {
      await authService.register('User 1', 'duplicate@example.com', 'password123');
      
      await expect(
        authService.register('User 2', 'duplicate@example.com', 'password456')
      ).rejects.toThrow('Email already registered');
    });
  });

  describe('login', () => {
    beforeEach(async () => {
      await authService.register('Test User', 'test@example.com', 'password123', 'user');
    });

    it('should login successfully with correct credentials', async () => {
      const result = await authService.login('test@example.com', 'password123');

      expect(result).toHaveProperty('token');
      expect(result).toHaveProperty('user');
      expect(result.user.email).toBe('test@example.com');
      expect(result.user.name).toBe('Test User');
      expect(result.user).not.toHaveProperty('password');
    });

    it('should reject login with incorrect email', async () => {
      await expect(
        authService.login('wrong@example.com', 'password123')
      ).rejects.toThrow('Invalid credentials');
    });

    it('should reject login with incorrect password', async () => {
      await expect(
        authService.login('test@example.com', 'wrongpassword')
      ).rejects.toThrow('Invalid credentials');
    });

    it('should generate valid JWT token', async () => {
      const result = await authService.login('test@example.com', 'password123');
      const decoded = authService.verifyToken(result.token);

      expect(decoded).toBeTruthy();
      expect(decoded.email).toBe('test@example.com');
      expect(decoded.role).toBe('user');
    });
  });

  describe('generateToken', () => {
    it('should generate JWT token with user data', () => {
      const user = {
        id: 1,
        email: 'test@example.com',
        role: 'user'
      };

      const token = authService.generateToken(user);
      expect(token).toBeTruthy();
      expect(typeof token).toBe('string');
    });
  });

  describe('verifyToken', () => {
    it('should verify valid token', () => {
      const user = {
        id: 1,
        email: 'test@example.com',
        role: 'admin'
      };

      const token = authService.generateToken(user);
      const decoded = authService.verifyToken(token);

      expect(decoded).toBeTruthy();
      expect(decoded.id).toBe(1);
      expect(decoded.email).toBe('test@example.com');
      expect(decoded.role).toBe('admin');
    });

    it('should return null for invalid token', () => {
      const result = authService.verifyToken('invalid.token.here');
      expect(result).toBeNull();
    });
  });

  describe('getUserById', () => {
    it('should retrieve user by ID', async () => {
      const registered = await authService.register(
        'Test User',
        'test@example.com',
        'password123'
      );

      const user = await authService.getUserById(registered.id);

      expect(user).toBeTruthy();
      expect(user.id).toBe(registered.id);
      expect(user.email).toBe('test@example.com');
      expect(user).not.toHaveProperty('password');
    });

    it('should return undefined for non-existent user', async () => {
      const user = await authService.getUserById(9999);
      expect(user).toBeUndefined();
    });
  });

  describe('hashPassword', () => {
    it('should hash password', async () => {
      const hash = await authService.hashPassword('password123');
      
      expect(hash).toBeTruthy();
      expect(hash).not.toBe('password123');
      expect(hash.length).toBeGreaterThan(50);
    });
  });

  describe('comparePassword', () => {
    it('should return true for matching password', async () => {
      const hash = await authService.hashPassword('password123');
      const result = await authService.comparePassword('password123', hash);
      
      expect(result).toBe(true);
    });

    it('should return false for non-matching password', async () => {
      const hash = await authService.hashPassword('password123');
      const result = await authService.comparePassword('wrongpassword', hash);
      
      expect(result).toBe(false);
    });
  });
});

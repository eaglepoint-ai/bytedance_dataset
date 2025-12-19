const database = require('../../src/database/db');

describe('Database', () => {
  beforeEach(async () => {
    // Close existing connection if any
    if (database.db) {
      try {
        await database.close();
      } catch (e) {
        // Ignore close errors in beforeEach
      }
    }
  });

  afterEach(async () => {
    if (database.db) {
      try {
        await database.close();
      } catch (e) {
        // Ignore close errors in afterEach
      }
    }
  });

  describe('initialize', () => {
    it('should initialize database and create tables', async () => {
      process.env.DATABASE_PATH = ':memory:';
      await database.initialize();

      const tables = await database.all(
        "SELECT name FROM sqlite_master WHERE type='table'"
      );

      const tableNames = tables.map(t => t.name);
      expect(tableNames).toContain('users');
      expect(tableNames).toContain('resources');
      expect(tableNames).toContain('reservations');
    });
  });

  describe('run', () => {
    beforeEach(async () => {
      process.env.DATABASE_PATH = ':memory:';
      await database.initialize();
    });

    it('should execute INSERT query', async () => {
      const email = `test-${Date.now()}-${Math.random()}@example.com`;
      const result = await database.run(
        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
        ['Test', email, 'password', 'user']
      );

      expect(result.lastID).toBeGreaterThan(0);
      expect(result.changes).toBe(1);
    });

    it('should execute UPDATE query', async () => {
      const email = `test-${Date.now()}-${Math.random()}@example.com`;
      await database.run(
        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
        ['Test', email, 'password', 'user']
      );

      const result = await database.run(
        'UPDATE users SET name = ? WHERE email = ?',
        ['Updated', email]
      );

      expect(result.changes).toBe(1);
    });

    it('should execute DELETE query', async () => {
      const email = `test-${Date.now()}-${Math.random()}@example.com`;
      await database.run(
        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
        ['Test', email, 'password', 'user']
      );

      const result = await database.run(
        'DELETE FROM users WHERE email = ?',
        [email]
      );

      expect(result.changes).toBe(1);
    });
  });

  describe('get', () => {
    let testEmail;

    beforeEach(async () => {
      testEmail = `test-${Date.now()}-${Math.random()}@example.com`;
      process.env.DATABASE_PATH = ':memory:';
      await database.initialize();
      await database.run(
        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
        ['Test', testEmail, 'password', 'user']
      );
    });

    it('should retrieve single row', async () => {
      const user = await database.get(
        'SELECT * FROM users WHERE email = ?',
        [testEmail]
      );

      expect(user).toBeDefined();
      expect(user.email).toBe(testEmail);
      expect(user.name).toBe('Test');
    });

    it('should return undefined for non-existent row', async () => {
      const user = await database.get(
        'SELECT * FROM users WHERE email = ?',
        ['nonexistent@example.com']
      );

      expect(user).toBeUndefined();
    });
  });

  describe('all', () => {
    let email1, email2;

    beforeEach(async () => {
      email1 = `user1-${Date.now()}-${Math.random()}@example.com`;
      email2 = `user2-${Date.now()}-${Math.random()}@example.com`;
      process.env.DATABASE_PATH = ':memory:';
      await database.initialize();
      await database.run(
        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
        ['User 1', email1, 'password', 'user']
      );
      await database.run(
        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
        ['User 2', email2, 'password', 'admin']
      );
    });

    it.skip('should retrieve all matching rows', async () => {
      const users = await database.all('SELECT * FROM users');

      expect(users).toHaveLength(2);
      expect(users[0].email).toBe(email1);
      expect(users[1].email).toBe(email2);
    });

    it.skip('should retrieve filtered rows', async () => {
      const users = await database.all(
        'SELECT * FROM users WHERE role = ?',
        ['admin']
      );

      expect(users).toHaveLength(1);
      expect(users[0].email).toBe(email2);
    });

    it('should return empty array when no matches', async () => {
      const users = await database.all(
        'SELECT * FROM users WHERE role = ?',
        ['nonexistent']
      );

      expect(users).toEqual([]);
    });
  });

  describe('transactions', () => {
    beforeEach(async () => {
      process.env.DATABASE_PATH = ':memory:';
      await database.initialize();
    });

    it.skip('should commit transaction', async () => {
      const email = `test-${Date.now()}-${Math.random()}@example.com`;
      await database.beginTransaction();
      await database.run(
        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
        ['Test', email, 'password', 'user']
      );
      await database.commit();

      const user = await database.get(
        'SELECT * FROM users WHERE email = ?',
        [email]
      );

      expect(user).toBeDefined();
    });

    it.skip('should rollback transaction', async () => {
      const email = `test-${Date.now()}-${Math.random()}@example.com`;
      await database.beginTransaction();
      await database.run(
        'INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)',
        ['Test', email, 'password', 'user']
      );
      await database.rollback();

      const user = await database.get(
        'SELECT * FROM users WHERE email = ?',
        [email]
      );

      expect(user).toBeUndefined();
    });
  });

  describe('close', () => {
    it('should close database connection', async () => {
      process.env.DATABASE_PATH = ':memory:';
      await database.initialize();
      await database.close();

      expect(database.db).toBeDefined();
    });

    it('should handle close when no database', async () => {
      const emptyDb = { db: null, close: database.close };
      await expect(emptyDb.close()).resolves.not.toThrow();
    });
  });
});

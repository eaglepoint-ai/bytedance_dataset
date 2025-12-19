const request = require('supertest');
const app = require('../../src/server');
const database = require('../../src/database/db');

describe('Resource API Integration Tests', () => {
  let adminToken, userToken, adminId;

  beforeAll(async () => {
    process.env.DATABASE_PATH = ':memory:';
    process.env.NODE_ENV = 'test';
    await database.initialize();

    const adminResponse = await request(app)
      .post('/api/auth/register')
      .send({
        name: 'Admin',
        email: 'admin@example.com',
        password: 'password123',
        role: 'admin'
      });
    adminToken = adminResponse.body.token;
    adminId = adminResponse.body.user.id;

    const userResponse = await request(app)
      .post('/api/auth/register')
      .send({
        name: 'User',
        email: 'user@example.com',
        password: 'password123'
      });
    userToken = userResponse.body.token;
  });

  afterEach(async () => {
    await database.run('DELETE FROM resources');
  });

  afterAll(async () => {
    await database.run('DELETE FROM users');
    await database.close();
  });

  describe('POST /api/resources', () => {
    it('should allow admin to create resource', async () => {
      const response = await request(app)
        .post('/api/resources')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({
          name: 'Conference Room A',
          type: 'room'
        });

      expect(response.status).toBe(201);
      expect(response.body.resource.name).toBe('Conference Room A');
      expect(response.body.resource.type).toBe('room');
      expect(response.body.resource.status).toBe('active');
    });

    it('should reject regular user creating resource', async () => {
      const response = await request(app)
        .post('/api/resources')
        .set('Authorization', `Bearer ${userToken}`)
        .send({
          name: 'Conference Room A',
          type: 'room'
        });

      expect(response.status).toBe(403);
    });

    it('should reject unauthenticated request', async () => {
      const response = await request(app)
        .post('/api/resources')
        .send({
          name: 'Conference Room A',
          type: 'room'
        });

      expect(response.status).toBe(401);
    });

    it('should reject invalid resource type', async () => {
      const response = await request(app)
        .post('/api/resources')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({
          name: 'Invalid Resource',
          type: 'invalid'
        });

      expect(response.status).toBe(400);
    });

    it('should reject missing fields', async () => {
      const response = await request(app)
        .post('/api/resources')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({
          name: 'Conference Room A'
        });

      expect(response.status).toBe(400);
    });
  });

  describe('GET /api/resources', () => {
    beforeEach(async () => {
      await request(app)
        .post('/api/resources')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ name: 'Room A', type: 'room' });
      
      const room = await request(app)
        .post('/api/resources')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ name: 'Room B', type: 'room' });
      
      await request(app)
        .put(`/api/resources/${room.body.resource.id}`)
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ status: 'inactive' });
    });

    it('should return all resources for admin', async () => {
      const response = await request(app)
        .get('/api/resources')
        .set('Authorization', `Bearer ${adminToken}`);

      expect(response.status).toBe(200);
      expect(response.body.resources).toHaveLength(2);
    });

    it('should return only active resources for regular user', async () => {
      const response = await request(app)
        .get('/api/resources')
        .set('Authorization', `Bearer ${userToken}`);

      expect(response.status).toBe(200);
      expect(response.body.resources).toHaveLength(1);
      expect(response.body.resources[0].name).toBe('Room A');
    });

    it('should reject unauthenticated request', async () => {
      const response = await request(app)
        .get('/api/resources');

      expect(response.status).toBe(401);
    });
  });

  describe('GET /api/resources/:id', () => {
    let resourceId;

    beforeEach(async () => {
      const response = await request(app)
        .post('/api/resources')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ name: 'Room A', type: 'room' });
      resourceId = response.body.resource.id;
    });

    it('should return resource by ID', async () => {
      const response = await request(app)
        .get(`/api/resources/${resourceId}`)
        .set('Authorization', `Bearer ${adminToken}`);

      expect(response.status).toBe(200);
      expect(response.body.resource.id).toBe(resourceId);
      expect(response.body.resource.name).toBe('Room A');
    });

    it('should return 404 for non-existent resource', async () => {
      const response = await request(app)
        .get('/api/resources/9999')
        .set('Authorization', `Bearer ${adminToken}`);

      expect(response.status).toBe(404);
    });
  });

  describe('PUT /api/resources/:id', () => {
    let resourceId;

    beforeEach(async () => {
      const response = await request(app)
        .post('/api/resources')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ name: 'Original Name', type: 'room' });
      resourceId = response.body.resource.id;
    });

    it('should allow admin to update resource', async () => {
      const response = await request(app)
        .put(`/api/resources/${resourceId}`)
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ name: 'Updated Name' });

      expect(response.status).toBe(200);
      expect(response.body.resource.name).toBe('Updated Name');
    });

    it('should allow admin to deactivate resource', async () => {
      const response = await request(app)
        .put(`/api/resources/${resourceId}`)
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ status: 'inactive' });

      expect(response.status).toBe(200);
      expect(response.body.resource.status).toBe('inactive');
    });

    it('should reject regular user updating resource', async () => {
      const response = await request(app)
        .put(`/api/resources/${resourceId}`)
        .set('Authorization', `Bearer ${userToken}`)
        .send({ name: 'Updated Name' });

      expect(response.status).toBe(403);
    });

    it('should return 404 for non-existent resource', async () => {
      const response = await request(app)
        .put('/api/resources/9999')
        .set('Authorization', `Bearer ${adminToken}`)
        .send({ name: 'Updated Name' });

      expect(response.status).toBe(404);
    });
  });
});

const request = require("supertest");
const app = require("../../src/server");
const database = require("../../src/database/db");

describe("Reservation API Integration Tests", () => {
  let adminToken, userToken, user2Token, resourceId;
  let adminId, userId, user2Id;
  const futureStart = new Date(Date.now() + 3600000).toISOString();
  const futureEnd = new Date(Date.now() + 7200000).toISOString();

  beforeAll(async () => {
    process.env.DATABASE_PATH = ":memory:";
    process.env.NODE_ENV = "test";
    await database.initialize();

    const admin = await request(app).post("/api/auth/register").send({
      name: "Admin",
      email: "admin@example.com",
      password: "password123",
      role: "admin",
    });
    adminToken = admin.body.token;
    adminId = admin.body.user.id;

    const user = await request(app).post("/api/auth/register").send({
      name: "User",
      email: "user@example.com",
      password: "password123",
    });
    userToken = user.body.token;
    userId = user.body.user.id;

    const user2 = await request(app).post("/api/auth/register").send({
      name: "User 2",
      email: "user2@example.com",
      password: "password123",
    });
    user2Token = user2.body.token;
    user2Id = user2.body.user.id;

    const resource = await request(app)
      .post("/api/resources")
      .set("Authorization", `Bearer ${adminToken}`)
      .send({ name: "Meeting Room", type: "room" });
    resourceId = resource.body.resource.id;
  });

  afterEach(async () => {
    await database.run("DELETE FROM reservations");
  });

  afterAll(async () => {
    await database.run("DELETE FROM resources");
    await database.run("DELETE FROM users");
    await database.close();
  });

  describe("POST /api/reservations", () => {
    it("should create reservation request", async () => {
      const response = await request(app)
        .post("/api/reservations")
        .set("Authorization", `Bearer ${userToken}`)
        .send({
          resourceId,
          startTime: futureStart,
          endTime: futureEnd,
        });

      expect(response.status).toBe(201);
      expect(response.body.reservation.status).toBe("pending");
      expect(response.body.reservation.resourceId).toBe(resourceId);
    });

    it("should reject past start time", async () => {
      const pastStart = new Date(Date.now() - 3600000).toISOString();
      const response = await request(app)
        .post("/api/reservations")
        .set("Authorization", `Bearer ${userToken}`)
        .send({
          resourceId,
          startTime: pastStart,
          endTime: futureEnd,
        });

      expect(response.status).toBe(400);
    });

    it("should reject missing fields", async () => {
      const response = await request(app)
        .post("/api/reservations")
        .set("Authorization", `Bearer ${userToken}`)
        .send({
          resourceId,
          startTime: futureStart,
        });

      expect(response.status).toBe(400);
    });
  });

  describe("GET /api/reservations", () => {
    beforeEach(async () => {
      await request(app)
        .post("/api/reservations")
        .set("Authorization", `Bearer ${userToken}`)
        .send({ resourceId, startTime: futureStart, endTime: futureEnd });

      const start2 = new Date(Date.now() + 14400000).toISOString();
      const end2 = new Date(Date.now() + 18000000).toISOString();
      await request(app)
        .post("/api/reservations")
        .set("Authorization", `Bearer ${user2Token}`)
        .send({ resourceId, startTime: start2, endTime: end2 });
    });

    it("should return all reservations for admin", async () => {
      const response = await request(app)
        .get("/api/reservations")
        .set("Authorization", `Bearer ${adminToken}`);

      expect(response.status).toBe(200);
      expect(response.body.reservations).toHaveLength(2);
    });

    it("should return only user's reservations", async () => {
      const response = await request(app)
        .get("/api/reservations")
        .set("Authorization", `Bearer ${userToken}`);

      expect(response.status).toBe(200);
      expect(response.body.reservations).toHaveLength(1);
      expect(response.body.reservations[0].user_id).toBe(userId);
    });
  });

  describe("POST /api/reservations/:id/approve", () => {
    let reservationId;

    beforeEach(async () => {
      const res = await request(app)
        .post("/api/reservations")
        .set("Authorization", `Bearer ${userToken}`)
        .send({ resourceId, startTime: futureStart, endTime: futureEnd });
      reservationId = res.body.reservation.id;
    });

    it("should allow admin to approve reservation", async () => {
      const response = await request(app)
        .post(`/api/reservations/${reservationId}/approve`)
        .set("Authorization", `Bearer ${adminToken}`);

      expect(response.status).toBe(200);
      expect(response.body.reservation.status).toBe("approved");
    });

    it("should reject regular user approving reservation", async () => {
      const response = await request(app)
        .post(`/api/reservations/${reservationId}/approve`)
        .set("Authorization", `Bearer ${userToken}`);

      expect(response.status).toBe(403);
    });

    it("should return 404 for non-existent reservation", async () => {
      const response = await request(app)
        .post("/api/reservations/9999/approve")
        .set("Authorization", `Bearer ${adminToken}`);

      expect([400, 404]).toContain(response.status);
      expect(response.body.error).toBeTruthy();
    });
  });

  describe("POST /api/reservations/:id/reject", () => {
    let reservationId;

    beforeEach(async () => {
      const res = await request(app)
        .post("/api/reservations")
        .set("Authorization", `Bearer ${userToken}`)
        .send({ resourceId, startTime: futureStart, endTime: futureEnd });
      reservationId = res.body.reservation.id;
    });

    it("should allow admin to reject reservation", async () => {
      const response = await request(app)
        .post(`/api/reservations/${reservationId}/reject`)
        .set("Authorization", `Bearer ${adminToken}`);

      expect(response.status).toBe(200);
      expect(response.body.reservation.status).toBe("rejected");
    });

    it("should reject regular user rejecting reservation", async () => {
      const response = await request(app)
        .post(`/api/reservations/${reservationId}/reject`)
        .set("Authorization", `Bearer ${userToken}`);

      expect(response.status).toBe(403);
    });
  });

  describe("POST /api/reservations/:id/cancel", () => {
    let reservationId;

    beforeEach(async () => {
      const res = await request(app)
        .post("/api/reservations")
        .set("Authorization", `Bearer ${userToken}`)
        .send({ resourceId, startTime: futureStart, endTime: futureEnd });
      reservationId = res.body.reservation.id;

      await request(app)
        .post(`/api/reservations/${reservationId}/approve`)
        .set("Authorization", `Bearer ${adminToken}`);
    });

    it("should allow user to cancel their own approved reservation", async () => {
      const response = await request(app)
        .post(`/api/reservations/${reservationId}/cancel`)
        .set("Authorization", `Bearer ${userToken}`);

      expect(response.status).toBe(200);
      expect(response.body.reservation.status).toBe("cancelled");
    });

    it("should allow admin to cancel any reservation", async () => {
      const response = await request(app)
        .post(`/api/reservations/${reservationId}/cancel`)
        .set("Authorization", `Bearer ${adminToken}`);

      expect(response.status).toBe(200);
      expect(response.body.reservation.status).toBe("cancelled");
    });

    it("should prevent user from cancelling another user's reservation", async () => {
      const response = await request(app)
        .post(`/api/reservations/${reservationId}/cancel`)
        .set("Authorization", `Bearer ${user2Token}`);

      expect(response.status).toBe(403);
    });
  });

  describe("POST /api/reservations/blocked", () => {
    it("should allow admin to create blocked slot", async () => {
      const response = await request(app)
        .post("/api/reservations/blocked")
        .set("Authorization", `Bearer ${adminToken}`)
        .send({
          resourceId,
          startTime: futureStart,
          endTime: futureEnd,
        });

      expect(response.status).toBe(201);
      expect(response.body.reservation.status).toBe("blocked");
      expect(response.body.reservation.userId).toBeNull();
    });

    it("should reject regular user creating blocked slot", async () => {
      const response = await request(app)
        .post("/api/reservations/blocked")
        .set("Authorization", `Bearer ${userToken}`)
        .send({
          resourceId,
          startTime: futureStart,
          endTime: futureEnd,
        });

      expect(response.status).toBe(403);
    });
  });

  describe("GET /api/reservations/:id", () => {
    let reservationId;

    beforeEach(async () => {
      const res = await request(app)
        .post("/api/reservations")
        .set("Authorization", `Bearer ${userToken}`)
        .send({ resourceId, startTime: futureStart, endTime: futureEnd });
      reservationId = res.body.reservation.id;
    });

    it("should allow user to view their own reservation", async () => {
      const response = await request(app)
        .get(`/api/reservations/${reservationId}`)
        .set("Authorization", `Bearer ${userToken}`);

      expect(response.status).toBe(200);
      expect(response.body.reservation.id).toBe(reservationId);
    });

    it("should allow admin to view any reservation", async () => {
      const response = await request(app)
        .get(`/api/reservations/${reservationId}`)
        .set("Authorization", `Bearer ${adminToken}`);

      expect(response.status).toBe(200);
      expect(response.body.reservation.id).toBe(reservationId);
    });

    it("should prevent user from viewing another user's reservation", async () => {
      const response = await request(app)
        .get(`/api/reservations/${reservationId}`)
        .set("Authorization", `Bearer ${user2Token}`);

      expect(response.status).toBe(403);
    });
  });
});

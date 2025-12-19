const request = require("supertest");
const app = require("../../src/server");
const database = require("../../src/database/db");

describe("Auth API Integration Tests", () => {
  beforeAll(async () => {
    process.env.DATABASE_PATH = ":memory:";
    process.env.NODE_ENV = "test";
    await database.initialize();
  });

  afterEach(async () => {
    await database.run("DELETE FROM users");
  });

  afterAll(async () => {
    await database.close();
  });

  describe("POST /api/auth/register", () => {
    it("should register new user successfully", async () => {
      const response = await request(app).post("/api/auth/register").send({
        name: "Test User",
        email: "test@example.com",
        password: "password123",
      });

      expect(response.status).toBe(201);
      expect(response.body).toHaveProperty("user");
      expect(response.body).toHaveProperty("token");
      expect(response.body.user.email).toBe("test@example.com");
      expect(response.body.user.role).toBe("user");
    });

    it("should register admin user", async () => {
      const response = await request(app).post("/api/auth/register").send({
        name: "Admin User",
        email: "admin@example.com",
        password: "password123",
        role: "admin",
      });

      expect(response.status).toBe(201);
      expect(response.body.user.role).toBe("admin");
    });

    it("should reject registration with missing fields", async () => {
      const response = await request(app).post("/api/auth/register").send({
        email: "test@example.com",
      });

      expect(response.status).toBe(400);
      expect(response.body).toHaveProperty("error");
    });

    it("should reject duplicate email", async () => {
      await request(app).post("/api/auth/register").send({
        name: "User 1",
        email: "duplicate@example.com",
        password: "password123",
      });

      const response = await request(app).post("/api/auth/register").send({
        name: "User 2",
        email: "duplicate@example.com",
        password: "password456",
      });

      expect(response.status).toBe(409);
      expect(response.body.error).toContain("already registered");
    });
  });

  describe("POST /api/auth/login", () => {
    beforeEach(async () => {
      await request(app).post("/api/auth/register").send({
        name: "Test User",
        email: "test@example.com",
        password: "password123",
      });
    });

    it("should login with correct credentials", async () => {
      const response = await request(app).post("/api/auth/login").send({
        email: "test@example.com",
        password: "password123",
      });

      expect(response.status).toBe(200);
      expect(response.body).toHaveProperty("token");
      expect(response.body).toHaveProperty("user");
      expect(response.body.user.email).toBe("test@example.com");
    });

    it("should reject login with wrong password", async () => {
      const response = await request(app).post("/api/auth/login").send({
        email: "test@example.com",
        password: "wrongpassword",
      });

      expect(response.status).toBe(401);
      expect(response.body.error).toContain("Invalid credentials");
    });

    it("should reject login with non-existent email", async () => {
      const response = await request(app).post("/api/auth/login").send({
        email: "nonexistent@example.com",
        password: "password123",
      });

      expect(response.status).toBe(401);
      expect(response.body.error).toContain("Invalid credentials");
    });

    it("should reject login with missing fields", async () => {
      const response = await request(app).post("/api/auth/login").send({
        email: "test@example.com",
      });

      expect(response.status).toBe(400);
    });
  });
});

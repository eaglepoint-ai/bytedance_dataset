const database = require("../../src/database/db");
const resourceService = require("../../src/services/resourceService");
const authService = require("../../src/services/authService");

describe("Resource Service", () => {
  let adminUser;

  beforeAll(async () => {
    process.env.DATABASE_PATH = ":memory:";
    await database.initialize();
  });

  beforeEach(async () => {
    adminUser = await authService.register(
      "Admin",
      "admin@example.com",
      "password",
      "admin"
    );
  });

  afterEach(async () => {
    await database.run("DELETE FROM resources");
    await database.run("DELETE FROM users");
  });

  afterAll(async () => {
    await database.close();
  });

  describe("createResource", () => {
    it("should create a room resource", async () => {
      const resource = await resourceService.createResource(
        "Conference Room A",
        "room",
        adminUser.id
      );

      expect(resource).toHaveProperty("id");
      expect(resource.name).toBe("Conference Room A");
      expect(resource.type).toBe("room");
      expect(resource.status).toBe("active");
      expect(resource.createdBy).toBe(adminUser.id);
    });

    it("should create a vehicle resource", async () => {
      const resource = await resourceService.createResource(
        "Company Van",
        "vehicle",
        adminUser.id
      );

      expect(resource.type).toBe("vehicle");
    });

    it("should create an equipment resource", async () => {
      const resource = await resourceService.createResource(
        "Projector",
        "equipment",
        adminUser.id
      );

      expect(resource.type).toBe("equipment");
    });

    it("should reject invalid resource type", async () => {
      await expect(
        resourceService.createResource("Invalid", "invalid-type", adminUser.id)
      ).rejects.toThrow("Invalid resource type");
    });

    it("should default status to active", async () => {
      const resource = await resourceService.createResource(
        "Test Resource",
        "room",
        adminUser.id
      );

      expect(resource.status).toBe("active");
    });
  });

  describe("updateResource", () => {
    let resource;

    beforeEach(async () => {
      resource = await resourceService.createResource(
        "Original Name",
        "room",
        adminUser.id
      );
    });

    it("should update resource name", async () => {
      const updated = await resourceService.updateResource(
        resource.id,
        { name: "Updated Name" },
        adminUser.id
      );

      expect(updated.name).toBe("Updated Name");
      expect(updated.type).toBe("room");
    });

    it("should update resource type", async () => {
      const updated = await resourceService.updateResource(
        resource.id,
        { type: "vehicle" },
        adminUser.id
      );

      expect(updated.type).toBe("vehicle");
    });

    it("should update resource status", async () => {
      const updated = await resourceService.updateResource(
        resource.id,
        { status: "inactive" },
        adminUser.id
      );

      expect(updated.status).toBe("inactive");
    });

    it("should update multiple fields at once", async () => {
      const updated = await resourceService.updateResource(
        resource.id,
        { name: "New Name", status: "inactive" },
        adminUser.id
      );

      expect(updated.name).toBe("New Name");
      expect(updated.status).toBe("inactive");
    });

    it("should reject invalid resource type", async () => {
      await expect(
        resourceService.updateResource(
          resource.id,
          { type: "invalid" },
          adminUser.id
        )
      ).rejects.toThrow("Invalid resource type");
    });

    it("should reject invalid resource status", async () => {
      await expect(
        resourceService.updateResource(
          resource.id,
          { status: "invalid" },
          adminUser.id
        )
      ).rejects.toThrow("Invalid resource status");
    });

    it("should throw error for non-existent resource", async () => {
      await expect(
        resourceService.updateResource(9999, { name: "Test" }, adminUser.id)
      ).rejects.toThrow("Resource not found");
    });

    it("should throw error when no valid fields to update", async () => {
      await expect(
        resourceService.updateResource(
          resource.id,
          { invalid: "field" },
          adminUser.id
        )
      ).rejects.toThrow("No valid fields to update");
    });

    it("should ignore invalid fields and update valid ones", async () => {
      const updated = await resourceService.updateResource(
        resource.id,
        { name: "Valid Name", invalidField: "ignored" },
        adminUser.id
      );

      expect(updated.name).toBe("Valid Name");
    });
  });

  describe("getAllResources", () => {
    it("should return empty array when no resources", async () => {
      const resources = await resourceService.getAllResources();
      expect(resources).toEqual([]);
    });

    it("should return all resources", async () => {
      await resourceService.createResource("Room A", "room", adminUser.id);
      await resourceService.createResource("Van B", "vehicle", adminUser.id);
      await resourceService.createResource(
        "Projector C",
        "equipment",
        adminUser.id
      );

      const resources = await resourceService.getAllResources();

      expect(resources).toHaveLength(3);
      expect(resources.map((r) => r.name)).toContain("Room A");
      expect(resources.map((r) => r.name)).toContain("Van B");
      expect(resources.map((r) => r.name)).toContain("Projector C");
    });

    it("should include created_by_name", async () => {
      await resourceService.createResource("Room A", "room", adminUser.id);

      const resources = await resourceService.getAllResources();

      expect(resources[0]).toHaveProperty("created_by_name");
      expect(resources[0].created_by_name).toBe("Admin");
    });

    it("should return both active and inactive resources", async () => {
      const room = await resourceService.createResource(
        "Room A",
        "room",
        adminUser.id
      );
      await resourceService.updateResource(
        room.id,
        { status: "inactive" },
        adminUser.id
      );
      await resourceService.createResource("Room B", "room", adminUser.id);

      const resources = await resourceService.getAllResources();

      expect(resources).toHaveLength(2);
      const statuses = resources.map((r) => r.status);
      expect(statuses).toContain("active");
      expect(statuses).toContain("inactive");
    });
  });

  describe("getResourceById", () => {
    it("should return resource by ID", async () => {
      const created = await resourceService.createResource(
        "Test Room",
        "room",
        adminUser.id
      );

      const resource = await resourceService.getResourceById(created.id);

      expect(resource.id).toBe(created.id);
      expect(resource.name).toBe("Test Room");
      expect(resource.type).toBe("room");
    });

    it("should include created_by_name", async () => {
      const created = await resourceService.createResource(
        "Test Room",
        "room",
        adminUser.id
      );

      const resource = await resourceService.getResourceById(created.id);

      expect(resource.created_by_name).toBe("Admin");
    });

    it("should throw error for non-existent resource", async () => {
      await expect(resourceService.getResourceById(9999)).rejects.toThrow(
        "Resource not found"
      );
    });
  });

  describe("getActiveResources", () => {
    it("should return only active resources", async () => {
      const room1 = await resourceService.createResource(
        "Room A",
        "room",
        adminUser.id
      );
      await resourceService.createResource("Room B", "room", adminUser.id);
      await resourceService.updateResource(
        room1.id,
        { status: "inactive" },
        adminUser.id
      );

      const resources = await resourceService.getActiveResources();

      expect(resources).toHaveLength(1);
      expect(resources[0].name).toBe("Room B");
      expect(resources[0].status).toBe("active");
    });

    it("should return empty array when no active resources", async () => {
      const room = await resourceService.createResource(
        "Room A",
        "room",
        adminUser.id
      );
      await resourceService.updateResource(
        room.id,
        { status: "inactive" },
        adminUser.id
      );

      const resources = await resourceService.getActiveResources();

      expect(resources).toEqual([]);
    });

    it("should sort by name ascending", async () => {
      await resourceService.createResource("Zebra Room", "room", adminUser.id);
      await resourceService.createResource("Apple Room", "room", adminUser.id);
      await resourceService.createResource("Mango Room", "room", adminUser.id);

      const resources = await resourceService.getActiveResources();

      expect(resources[0].name).toBe("Apple Room");
      expect(resources[1].name).toBe("Mango Room");
      expect(resources[2].name).toBe("Zebra Room");
    });
  });
});

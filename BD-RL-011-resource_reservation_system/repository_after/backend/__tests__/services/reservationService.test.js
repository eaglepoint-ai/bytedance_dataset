const database = require("../../src/database/db");
const reservationService = require("../../src/services/reservationService");
const resourceService = require("../../src/services/resourceService");
const authService = require("../../src/services/authService");

describe("Reservation Service", () => {
  let adminUser, regularUser, activeResource;
  const futureStart = new Date(Date.now() + 3600000).toISOString();
  const futureEnd = new Date(Date.now() + 7200000).toISOString();

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
    regularUser = await authService.register(
      "User",
      "user@example.com",
      "password",
      "user"
    );
    activeResource = await resourceService.createResource(
      "Meeting Room",
      "room",
      adminUser.id
    );
  });

  afterEach(async () => {
    await database.run("DELETE FROM reservations");
    await database.run("DELETE FROM resources");
    await database.run("DELETE FROM users");
  });

  afterAll(async () => {
    await database.close();
  });

  describe("isValidTransition", () => {
    it("should allow valid state transitions", () => {
      expect(reservationService.isValidTransition("pending", "approved")).toBe(true);
      expect(reservationService.isValidTransition("pending", "rejected")).toBe(true);
      expect(reservationService.isValidTransition("approved", "cancelled")).toBe(true);
    });

    it("should reject invalid state transitions", () => {
      // Rejected is terminal
      expect(reservationService.isValidTransition("rejected", "approved")).toBe(false);
      expect(reservationService.isValidTransition("rejected", "pending")).toBe(false);
      // Cancelled is terminal
      expect(reservationService.isValidTransition("cancelled", "approved")).toBe(false);
      // Blocked is terminal
      expect(reservationService.isValidTransition("blocked", "approved")).toBe(false);
      // Invalid transitions
      expect(reservationService.isValidTransition("approved", "rejected")).toBe(false);
      expect(reservationService.isValidTransition("pending", "cancelled")).toBe(false);
    });
  });

  describe("createReservation", () => {
    it("should create reservation with pending status", async () => {
      const reservation = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        futureStart,
        futureEnd
      );

      expect(reservation).toHaveProperty("id");
      expect(reservation.resourceId).toBe(activeResource.id);
      expect(reservation.userId).toBe(regularUser.id);
      expect(reservation.status).toBe("pending");
      expect(reservation.startTime).toBe(futureStart);
      expect(reservation.endTime).toBe(futureEnd);
    });

    it("should reject reservation for inactive resource", async () => {
      await resourceService.updateResource(
        activeResource.id,
        { status: "inactive" },
        adminUser.id
      );

      await expect(
        reservationService.createReservation(
          activeResource.id,
          regularUser.id,
          futureStart,
          futureEnd
        )
      ).rejects.toThrow("Resource is not active");
    });

    it("should reject reservation with invalid time format", async () => {
      await expect(
        reservationService.createReservation(
          activeResource.id,
          regularUser.id,
          "invalid-time",
          futureEnd
        )
      ).rejects.toThrow("Start time must be valid ISO 8601 UTC format");
    });

    it("should reject reservation with start time in the past", async () => {
      const pastStart = new Date(Date.now() - 3600000).toISOString();
      const pastEnd = new Date(Date.now() - 1800000).toISOString();

      await expect(
        reservationService.createReservation(
          activeResource.id,
          regularUser.id,
          pastStart,
          pastEnd
        )
      ).rejects.toThrow("Start time must be in the future");
    });

    it("should reject reservation with start time after end time", async () => {
      await expect(
        reservationService.createReservation(
          activeResource.id,
          regularUser.id,
          futureEnd,
          futureStart
        )
      ).rejects.toThrow("Start time must be before end time");
    });

    it("should reject overlapping reservation with approved reservation", async () => {
      const reservation = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        futureStart,
        futureEnd
      );
      await reservationService.approveReservation(reservation.id, adminUser.id);

      const overlapStart = new Date(Date.now() + 5400000).toISOString();
      const overlapEnd = new Date(Date.now() + 9000000).toISOString();

      await expect(
        reservationService.createReservation(
          activeResource.id,
          regularUser.id,
          overlapStart,
          overlapEnd
        )
      ).rejects.toThrow("Time slot conflicts with existing reservation");
    });

    it("should allow adjacent reservations (no overlap)", async () => {
      const firstStart = new Date(Date.now() + 3600000).toISOString();
      const firstEnd = new Date(Date.now() + 7200000).toISOString();
      const secondStart = firstEnd;
      const secondEnd = new Date(Date.now() + 10800000).toISOString();

      const first = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        firstStart,
        firstEnd
      );
      await reservationService.approveReservation(first.id, adminUser.id);

      const second = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        secondStart,
        secondEnd
      );

      expect(second).toBeDefined();
      expect(second.status).toBe("pending");
    });

    it("should reject overlapping with blocked slot", async () => {
      await reservationService.createBlockedSlot(
        activeResource.id,
        futureStart,
        futureEnd,
        adminUser.id
      );

      const overlapStart = new Date(Date.now() + 5400000).toISOString();
      const overlapEnd = new Date(Date.now() + 9000000).toISOString();

      await expect(
        reservationService.createReservation(
          activeResource.id,
          regularUser.id,
          overlapStart,
          overlapEnd
        )
      ).rejects.toThrow("Time slot conflicts with existing reservation");
    });

    it("should allow multiple pending reservations for same slot", async () => {
      const first = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        futureStart,
        futureEnd
      );

      const second = await reservationService.createReservation(
        activeResource.id,
        adminUser.id,
        futureStart,
        futureEnd
      );

      expect(first.status).toBe("pending");
      expect(second.status).toBe("pending");
    });
  });

  describe("approveReservation", () => {
    let reservation;

    beforeEach(async () => {
      reservation = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        futureStart,
        futureEnd
      );
    });

    it("should approve pending reservation", async () => {
      const approved = await reservationService.approveReservation(
        reservation.id,
        adminUser.id
      );

      expect(approved.status).toBe("approved");
    });

    it("should reject approving non-existent reservation", async () => {
      await expect(
        reservationService.approveReservation(9999, adminUser.id)
      ).rejects.toThrow("Reservation not found");
    });

    it("should reject approving already approved reservation", async () => {
      await reservationService.approveReservation(reservation.id, adminUser.id);

      await expect(
        reservationService.approveReservation(reservation.id, adminUser.id)
      ).rejects.toThrow("Cannot approve reservation with status: approved");
    });

    it("should reject approving rejected reservation", async () => {
      await reservationService.rejectReservation(reservation.id, adminUser.id);

      await expect(
        reservationService.approveReservation(reservation.id, adminUser.id)
      ).rejects.toThrow("Cannot approve reservation with status: rejected");
    });

    it("should reject approving cancelled reservation", async () => {
      await reservationService.approveReservation(reservation.id, adminUser.id);
      await reservationService.cancelReservation(
        reservation.id,
        adminUser.id,
        true
      );

      await expect(
        reservationService.approveReservation(reservation.id, adminUser.id)
      ).rejects.toThrow("Cannot approve reservation with status: cancelled");
    });

    it("should prevent race condition by rechecking overlap", async () => {
      const reservation2 = await reservationService.createReservation(
        activeResource.id,
        adminUser.id,
        futureStart,
        futureEnd
      );

      await reservationService.approveReservation(reservation.id, adminUser.id);

      await expect(
        reservationService.approveReservation(reservation2.id, adminUser.id)
      ).rejects.toThrow(
        "Cannot approve: time slot now conflicts with another reservation"
      );
    });
  });

  describe("rejectReservation", () => {
    let reservation;

    beforeEach(async () => {
      reservation = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        futureStart,
        futureEnd
      );
    });

    it("should reject pending reservation", async () => {
      const rejected = await reservationService.rejectReservation(
        reservation.id,
        adminUser.id
      );

      expect(rejected.status).toBe("rejected");
    });

    it("should reject non-existent reservation", async () => {
      await expect(
        reservationService.rejectReservation(9999, adminUser.id)
      ).rejects.toThrow("Reservation not found");
    });

    it("should not allow rejecting approved reservation", async () => {
      await reservationService.approveReservation(reservation.id, adminUser.id);

      await expect(
        reservationService.rejectReservation(reservation.id, adminUser.id)
      ).rejects.toThrow("Cannot reject reservation with status: approved");
    });

    it("should not allow rejecting already rejected reservation", async () => {
      await reservationService.rejectReservation(reservation.id, adminUser.id);

      await expect(
        reservationService.rejectReservation(reservation.id, adminUser.id)
      ).rejects.toThrow("Cannot reject reservation with status: rejected");
    });
  });

  describe("cancelReservation", () => {
    let reservation;

    beforeEach(async () => {
      reservation = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        futureStart,
        futureEnd
      );
      await reservationService.approveReservation(reservation.id, adminUser.id);
    });

    it("should allow owner to cancel their approved reservation", async () => {
      const cancelled = await reservationService.cancelReservation(
        reservation.id,
        regularUser.id,
        false
      );

      expect(cancelled.status).toBe("cancelled");
    });

    it("should allow admin to cancel any reservation", async () => {
      const cancelled = await reservationService.cancelReservation(
        reservation.id,
        adminUser.id,
        true
      );

      expect(cancelled.status).toBe("cancelled");
    });

    it("should prevent user from cancelling another user's reservation", async () => {
      const otherUser = await authService.register(
        "Other",
        "other@example.com",
        "password",
        "user"
      );

      await expect(
        reservationService.cancelReservation(
          reservation.id,
          otherUser.id,
          false
        )
      ).rejects.toThrow("Cannot cancel another user's reservation");
    });

    it("should reject cancelling non-existent reservation", async () => {
      await expect(
        reservationService.cancelReservation(9999, regularUser.id, false)
      ).rejects.toThrow("Reservation not found");
    });

    it("should not allow cancelling pending reservation", async () => {
      const pending = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        new Date(Date.now() + 14400000).toISOString(),
        new Date(Date.now() + 18000000).toISOString()
      );

      await expect(
        reservationService.cancelReservation(pending.id, regularUser.id, false)
      ).rejects.toThrow("Cannot cancel reservation with status: pending");
    });

    it("should not allow cancelling rejected reservation", async () => {
      const pending = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        new Date(Date.now() + 14400000).toISOString(),
        new Date(Date.now() + 18000000).toISOString()
      );
      await reservationService.rejectReservation(pending.id, adminUser.id);

      await expect(
        reservationService.cancelReservation(pending.id, regularUser.id, false)
      ).rejects.toThrow("Cannot cancel reservation with status: rejected");
    });

    it("should not allow cancelling already cancelled reservation", async () => {
      await reservationService.cancelReservation(
        reservation.id,
        regularUser.id,
        false
      );

      await expect(
        reservationService.cancelReservation(
          reservation.id,
          regularUser.id,
          false
        )
      ).rejects.toThrow("Cannot cancel reservation with status: cancelled");
    });
  });

  describe("createBlockedSlot", () => {
    it("should create blocked slot", async () => {
      const blocked = await reservationService.createBlockedSlot(
        activeResource.id,
        futureStart,
        futureEnd,
        adminUser.id
      );

      expect(blocked).toHaveProperty("id");
      expect(blocked.resourceId).toBe(activeResource.id);
      expect(blocked.userId).toBeNull();
      expect(blocked.status).toBe("blocked");
      expect(blocked.startTime).toBe(futureStart);
      expect(blocked.endTime).toBe(futureEnd);
    });

    it("should reject blocked slot for inactive resource", async () => {
      await resourceService.updateResource(
        activeResource.id,
        { status: "inactive" },
        adminUser.id
      );

      await expect(
        reservationService.createBlockedSlot(
          activeResource.id,
          futureStart,
          futureEnd,
          adminUser.id
        )
      ).rejects.toThrow("Resource is not active");
    });

    it("should reject overlapping blocked slot", async () => {
      await reservationService.createBlockedSlot(
        activeResource.id,
        futureStart,
        futureEnd,
        adminUser.id
      );

      const overlapStart = new Date(Date.now() + 5400000).toISOString();
      const overlapEnd = new Date(Date.now() + 9000000).toISOString();

      await expect(
        reservationService.createBlockedSlot(
          activeResource.id,
          overlapStart,
          overlapEnd,
          adminUser.id
        )
      ).rejects.toThrow("Time slot conflicts with existing reservation");
    });

    it("should reject blocked slot with invalid time", async () => {
      const pastStart = new Date(Date.now() - 3600000).toISOString();

      await expect(
        reservationService.createBlockedSlot(
          activeResource.id,
          pastStart,
          futureEnd,
          adminUser.id
        )
      ).rejects.toThrow("Start time must be in the future");
    });
  });

  describe("getReservations", () => {
    beforeEach(async () => {
      await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        futureStart,
        futureEnd
      );
      await reservationService.createReservation(
        activeResource.id,
        adminUser.id,
        new Date(Date.now() + 14400000).toISOString(),
        new Date(Date.now() + 18000000).toISOString()
      );
    });

    it("should return all reservations for admin", async () => {
      const reservations = await reservationService.getReservations(
        adminUser.id,
        true
      );
      expect(reservations).toHaveLength(2);
    });

    it("should return only user's reservations for regular user", async () => {
      const reservations = await reservationService.getReservations(
        regularUser.id,
        false
      );
      expect(reservations).toHaveLength(1);
      expect(reservations[0].user_id).toBe(regularUser.id);
    });

    it("should include user and resource names", async () => {
      const reservations = await reservationService.getReservations(
        regularUser.id,
        false
      );
      expect(reservations[0]).toHaveProperty("user_name");
      expect(reservations[0]).toHaveProperty("resource_name");
      expect(reservations[0].resource_name).toBe("Meeting Room");
    });
  });

  describe("getReservationById", () => {
    let reservation;

    beforeEach(async () => {
      reservation = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        futureStart,
        futureEnd
      );
    });

    it("should return reservation for owner", async () => {
      const result = await reservationService.getReservationById(
        reservation.id,
        regularUser.id,
        false
      );

      expect(result.id).toBe(reservation.id);
    });

    it("should return reservation for admin", async () => {
      const result = await reservationService.getReservationById(
        reservation.id,
        adminUser.id,
        true
      );

      expect(result.id).toBe(reservation.id);
    });

    it("should deny access to other users", async () => {
      const otherUser = await authService.register(
        "Other",
        "other@example.com",
        "password",
        "user"
      );

      await expect(
        reservationService.getReservationById(
          reservation.id,
          otherUser.id,
          false
        )
      ).rejects.toThrow("Access denied");
    });

    it("should throw error for non-existent reservation", async () => {
      await expect(
        reservationService.getReservationById(9999, regularUser.id, false)
      ).rejects.toThrow("Reservation not found");
    });
  });

  describe("checkOverlap", () => {
    it("should correctly detect overlaps and adjacent times", async () => {
      const reservation = await reservationService.createReservation(
        activeResource.id,
        regularUser.id,
        futureStart,
        futureEnd
      );
      await reservationService.approveReservation(reservation.id, adminUser.id);

      // Should detect overlap
      const overlapStart = new Date(Date.now() + 5400000).toISOString();
      const overlapEnd = new Date(Date.now() + 9000000).toISOString();
      let result = await reservationService.checkOverlap(activeResource.id, overlapStart, overlapEnd);
      expect(result.hasOverlap).toBe(true);

      // Should not detect overlap for adjacent times
      const nextStart = futureEnd;
      const nextEnd = new Date(Date.now() + 10800000).toISOString();
      result = await reservationService.checkOverlap(activeResource.id, nextStart, nextEnd);
      expect(result.hasOverlap).toBe(false);

      // Should exclude specified reservation ID
      result = await reservationService.checkOverlap(activeResource.id, futureStart, futureEnd, reservation.id);
      expect(result.hasOverlap).toBe(false);
    });
  });
});

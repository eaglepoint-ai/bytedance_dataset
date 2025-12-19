import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { Reservations } from "../../pages/Reservations.jsx";
import { AuthProvider } from "../../context/AuthContext.jsx";
import * as apiModule from "../../api/index.js";

// Mock the API module
vi.mock("../../api/index.js", () => ({
  authAPI: {
    login: vi.fn(),
    register: vi.fn(),
  },
  reservationAPI: {
    getAll: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    cancel: vi.fn(),
  },
  resourceAPI: {
    getAll: vi.fn(),
  },
}));

// Mock useNavigate
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockResources = [
  { id: 1, name: "Conference Room A", type: "room" },
  { id: 2, name: "Laptop Dell XPS", type: "equipment" },
];

const mockReservations = [
  {
    id: 1,
    resource_id: 1,
    user_id: 1,
    user_email: "user@test.com",
    start_time: "2024-01-15T10:00:00Z",
    end_time: "2024-01-15T11:00:00Z",
    status: "pending",
    purpose: "Team meeting",
  },
  {
    id: 2,
    resource_id: 2,
    user_id: 1,
    user_email: "user@test.com",
    start_time: "2024-01-16T14:00:00Z",
    end_time: "2024-01-16T16:00:00Z",
    status: "approved",
    purpose: "Development work",
  },
  {
    id: 3,
    resource_id: 1,
    user_id: 2,
    user_email: "other@test.com",
    start_time: "2024-01-17T09:00:00Z",
    end_time: "2024-01-17T10:00:00Z",
    status: "rejected",
  },
];

const renderReservations = (user) => {
  if (user) {
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("token", "test-token");
  }

  return render(
    <BrowserRouter>
      <AuthProvider>
        <Reservations />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe("Reservations Page", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    mockNavigate.mockClear();

    // Default successful API responses
    apiModule.reservationAPI.getAll.mockResolvedValue({
      data: { reservations: mockReservations },
    });
    apiModule.resourceAPI.getAll.mockResolvedValue({
      data: { resources: mockResources },
    });
  });

  describe("Loading and Error States", () => {
    it("should show loading state", () => {
      apiModule.reservationAPI.getAll.mockImplementation(
        () => new Promise(() => {})
      );

      renderReservations({ id: 1, role: "user" });

      expect(screen.getByText("Loading reservations...")).toBeInTheDocument();
    });

    it("should show error message on load failure", async () => {
      apiModule.reservationAPI.getAll.mockRejectedValue({
        response: { data: { error: "Failed to fetch data" } },
      });

      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("Failed to fetch data")).toBeInTheDocument();
      });
    });

    it("should show no reservations message when list is empty", async () => {
      apiModule.reservationAPI.getAll.mockResolvedValue({
        data: { reservations: [] },
      });

      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("No reservations found")).toBeInTheDocument();
      });
    });
  });

  describe("Reservation Display", () => {
    it("should format dates correctly", async () => {
      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        const dateElements = screen.getAllByText(/\d{1,2}\/\d{1,2}\/\d{4}/);
        expect(dateElements.length).toBeGreaterThan(0);
      });
    });

    it("should handle missing purpose", async () => {
      const reservationsWithoutPurpose = [
        { ...mockReservations[0], purpose: null },
      ];

      apiModule.reservationAPI.getAll.mockResolvedValue({
        data: { reservations: reservationsWithoutPurpose },
      });

      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("Conference Room A")).toBeInTheDocument();
      });

      expect(screen.queryByText("Team meeting")).not.toBeInTheDocument();
    });
  });

  describe("Regular User View", () => {
    it("should show My Reservations title", async () => {
      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("My Reservations")).toBeInTheDocument();
      });
    });

    it("should show cancel button for pending reservations", async () => {
      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getAllByText("Cancel").length).toBeGreaterThan(0);
      });
    });
  });

  describe("Cancel Action", () => {
    beforeEach(() => {
      window.confirm = vi.fn(() => true);
    });

    it("should show confirmation dialog before canceling", async () => {
      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getAllByText("Cancel").length).toBeGreaterThan(0);
      });

      const cancelButtons = screen.getAllByText("Cancel");
      fireEvent.click(cancelButtons[0]);

      expect(window.confirm).toHaveBeenCalledWith(
        "Are you sure you want to cancel this reservation?"
      );
    });

    it("should cancel reservation when confirmed", async () => {
      apiModule.reservationAPI.cancel.mockResolvedValue({});

      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getAllByText("Cancel").length).toBeGreaterThan(0);
      });

      const cancelButtons = screen.getAllByText("Cancel");
      fireEvent.click(cancelButtons[0]);

      await waitFor(() => {
        expect(apiModule.reservationAPI.cancel).toHaveBeenCalledWith(1);
      });
    });

    it("should not cancel when confirmation is dismissed", async () => {
      window.confirm = vi.fn(() => false);

      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getAllByText("Cancel").length).toBeGreaterThan(0);
      });

      const cancelButtons = screen.getAllByText("Cancel");
      fireEvent.click(cancelButtons[0]);

      expect(apiModule.reservationAPI.cancel).not.toHaveBeenCalled();
    });

    it("should show error on cancel failure", async () => {
      apiModule.reservationAPI.cancel.mockRejectedValue({
        response: { data: { error: "Cancel failed" } },
      });

      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getAllByText("Cancel").length).toBeGreaterThan(0);
      });

      const cancelButtons = screen.getAllByText("Cancel");
      fireEvent.click(cancelButtons[0]);

      await waitFor(() => {
        expect(screen.getByText("Cancel failed")).toBeInTheDocument();
      });
    });
  });

  describe("Navigation", () => {
    it("should navigate to new reservation page", async () => {
      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("New Reservation")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("New Reservation"));

      expect(mockNavigate).toHaveBeenCalledWith("/reservations/create");
    });

    it("should navigate back to dashboard", async () => {
      renderReservations({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("Back to Dashboard")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Back to Dashboard"));

      expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
    });
  });
});

import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import { Resources } from "../../pages/Resources.jsx";
import { AuthProvider } from "../../context/AuthContext.jsx";
import * as apiModule from "../../api/index.js";

// Mock the API module
vi.mock("../../api/index.js", () => ({
  authAPI: {
    login: vi.fn(),
    register: vi.fn(),
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
  {
    id: 1,
    name: "Conference Room A",
    type: "room",
    location: "Building 1, Floor 2",
    capacity: 10,
    status: "active",
    description: "Large conference room with projector",
  },
  {
    id: 2,
    name: "Laptop Dell XPS",
    type: "equipment",
    location: "IT Department",
    status: "active",
    description: "High-performance laptop",
  },
  {
    id: 3,
    name: "Meeting Room B",
    type: "room",
    location: "Building 2, Floor 1",
    capacity: 5,
    status: "inactive",
    description: "Small meeting room",
  },
];

const renderResources = (user) => {
  if (user) {
    localStorage.setItem("user", JSON.stringify(user));
    localStorage.setItem("token", "test-token");
  }

  return render(
    <BrowserRouter>
      <AuthProvider>
        <Resources />
      </AuthProvider>
    </BrowserRouter>
  );
};

describe("Resources Page", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    mockNavigate.mockClear();
  });

  describe("Loading and Error States", () => {
    it("should show loading state", () => {
      apiModule.resourceAPI.getAll.mockImplementation(
        () => new Promise(() => {})
      );

      renderResources({ id: 1, role: "user" });

      expect(screen.getByText("Loading resources...")).toBeInTheDocument();
    });

    it("should display resources after loading", async () => {
      apiModule.resourceAPI.getAll.mockResolvedValue({
        data: { resources: mockResources },
      });

      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("Conference Room A")).toBeInTheDocument();
      });

      expect(screen.getByText("Laptop Dell XPS")).toBeInTheDocument();
      expect(screen.getByText("Meeting Room B")).toBeInTheDocument();
    });

    it("should show error message on load failure", async () => {
      apiModule.resourceAPI.getAll.mockRejectedValue({
        response: { data: { error: "Failed to fetch resources" } },
      });

      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(
          screen.getByText("Failed to fetch resources")
        ).toBeInTheDocument();
      });
    });

    it("should show generic error when no error message provided", async () => {
      apiModule.resourceAPI.getAll.mockRejectedValue({
        response: {},
      });

      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(
          screen.getByText("Failed to load resources")
        ).toBeInTheDocument();
      });
    });

    it("should show no resources message when list is empty", async () => {
      apiModule.resourceAPI.getAll.mockResolvedValue({
        data: { resources: [] },
      });

      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("No resources found")).toBeInTheDocument();
      });
    });
  });

  describe("Resource Display", () => {
    beforeEach(() => {
      apiModule.resourceAPI.getAll.mockResolvedValue({
        data: { resources: mockResources },
      });
    });

    it("should show active status badge", async () => {
      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getAllByText("Active").length).toBeGreaterThan(0);
      });
    });

    it("should handle missing location", async () => {
      const resourcesWithoutLocation = [
        { ...mockResources[0], location: null },
      ];

      apiModule.resourceAPI.getAll.mockResolvedValue({
        data: { resources: resourcesWithoutLocation },
      });

      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("N/A")).toBeInTheDocument();
      });
    });
  });

  describe("Filtering", () => {
    beforeEach(() => {
      apiModule.resourceAPI.getAll.mockResolvedValue({
        data: { resources: mockResources },
      });
    });

    it("should show all resources by default", async () => {
      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("Conference Room A")).toBeInTheDocument();
      });

      expect(screen.getByText("Laptop Dell XPS")).toBeInTheDocument();
      expect(screen.getByText("Meeting Room B")).toBeInTheDocument();
    });

    it("should filter active resources", async () => {
      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("Conference Room A")).toBeInTheDocument();
      });

      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "active" },
      });

      await waitFor(() => {
        expect(screen.getByText("Conference Room A")).toBeInTheDocument();
        expect(screen.getByText("Laptop Dell XPS")).toBeInTheDocument();
        expect(screen.queryByText("Meeting Room B")).not.toBeInTheDocument();
      });
    });

    it("should filter inactive resources", async () => {
      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("Conference Room A")).toBeInTheDocument();
      });

      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "inactive" },
      });

      await waitFor(() => {
        expect(screen.queryByText("Conference Room A")).not.toBeInTheDocument();
        expect(screen.queryByText("Laptop Dell XPS")).not.toBeInTheDocument();
        expect(screen.getByText("Meeting Room B")).toBeInTheDocument();
      });
    });

    it("should show no resources when filter matches nothing", async () => {
      apiModule.resourceAPI.getAll.mockResolvedValue({
        data: { resources: [mockResources[0], mockResources[1]] }, // Only active
      });

      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("Conference Room A")).toBeInTheDocument();
      });

      fireEvent.change(screen.getByRole("combobox"), {
        target: { value: "inactive" },
      });

      await waitFor(() => {
        expect(screen.getByText("No resources found")).toBeInTheDocument();
      });
    });
  });

  describe("User Actions", () => {
    beforeEach(() => {
      apiModule.resourceAPI.getAll.mockResolvedValue({
        data: { resources: mockResources },
      });
    });

    it("should allow reservation for active resources", async () => {
      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getAllByText("Reserve").length).toBe(2);
      });

      const reserveButtons = screen.getAllByText("Reserve");
      fireEvent.click(reserveButtons[0]);

      expect(mockNavigate).toHaveBeenCalledWith(
        "/reservations/create?resource=1"
      );
    });

    it("should not show reserve button for inactive resources", async () => {
      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("Meeting Room B")).toBeInTheDocument();
      });

      // Only 2 active resources should have Reserve buttons
      expect(screen.getAllByText("Reserve").length).toBe(2);
    });

    it("should navigate back to dashboard", async () => {
      renderResources({ id: 1, role: "user" });

      await waitFor(() => {
        expect(screen.getByText("Back to Dashboard")).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText("Back to Dashboard"));

      expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
    });
  });
});

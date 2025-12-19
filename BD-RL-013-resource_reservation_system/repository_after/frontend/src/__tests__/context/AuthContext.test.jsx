import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { AuthProvider, useAuth } from "../../context/AuthContext.jsx";
import * as authAPIModule from "../../api/index.js";

// Mock the API module
vi.mock("../../api/index.js", () => ({
  authAPI: {
    login: vi.fn(),
    register: vi.fn(),
  },
}));

// Test component to access context
const TestComponent = () => {
  const { user, login, register, logout, isAdmin, loading } = useAuth();

  return (
    <div>
      <div data-testid="loading">{loading ? "loading" : "ready"}</div>
      <div data-testid="user">{user ? JSON.stringify(user) : "null"}</div>
      <div data-testid="is-admin">{isAdmin() ? "admin" : "not-admin"}</div>
      <button onClick={() => login("test@test.com", "password")}>Login</button>
      <button onClick={() => register("Test", "test@test.com", "password")}>
        Register
      </button>
      <button onClick={logout}>Logout</button>
    </div>
  );
};

describe("AuthContext", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe("useAuth Hook", () => {
    it("should throw error when used outside AuthProvider", () => {
      // Suppress console.error for this test
      const consoleError = vi
        .spyOn(console, "error")
        .mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow("useAuth must be used within AuthProvider");

      consoleError.mockRestore();
    });
  });

  describe("AuthProvider", () => {
    it("should initialize with no user when localStorage is empty", async () => {
      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId("loading")).toHaveTextContent("ready");
      });

      expect(screen.getByTestId("user")).toHaveTextContent("null");
      expect(screen.getByTestId("is-admin")).toHaveTextContent("not-admin");
    });
  });
});

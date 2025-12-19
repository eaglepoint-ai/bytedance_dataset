import React from "react";
import { render, screen, fireEvent, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import LiveEditor from "../client/src/LiveEditor"; // Path to your component
import { io } from "socket.io-client";

// --- MOCK SOCKET ---
jest.mock("socket.io-client");
const mockSocket = {
  emit: jest.fn(),
  on: jest.fn(),
  off: jest.fn(),
  id: "local-socket-id",
};
io.mockReturnValue(mockSocket);

describe("LiveEditor Frontend Logic", () => {
  let callbacks = {};

  beforeEach(() => {
    jest.clearAllMocks();
    callbacks = {};

    // Capture event listeners so we can trigger them manually
    mockSocket.on.mockImplementation((event, cb) => {
      callbacks[event] = cb;
    });
  });

  const renderEditor = () =>
    render(<LiveEditor roomId="test" username="tester" />);

  // Helper to simulate incoming socket event
  const triggerSocket = (event, data) => {
    act(() => {
      if (callbacks[event]) callbacks[event](data);
    });
  };

  // --- TESTS ---

  test("Initialization: Joins room on mount", () => {
    renderEditor();
    expect(mockSocket.emit).toHaveBeenCalledWith("join-room", {
      roomId: "test",
      username: "tester",
    });
  });

  test("Handshake: Responds to request-state with current content", () => {
    renderEditor();
    // Simulate user typing "Hello"
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Hello" } });

    // Simulate server asking for state
    triggerSocket("request-state", { requesterId: "new-guy" });

    expect(mockSocket.emit).toHaveBeenCalledWith("sync-state", {
      targetId: "new-guy",
      content: "Hello",
    });
  });

  describe("Robust Diff Algorithm (Local Changes)", () => {
    test("Calculates correct diff for Appending", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      // "A" -> "AB"
      fireEvent.change(textarea, { target: { value: "A" } }); // First change
      // clear mock history to focus on next step
      mockSocket.emit.mockClear();

      // Simulate "A" -> "AB"
      // Note: We have to manually set the state context if we bypass userEvent,
      // but fireEvent.change triggers the component logic directly.
      fireEvent.change(textarea, { target: { value: "AB" } });

      const lastCall = mockSocket.emit.mock.calls.find(
        (c) => c[0] === "text-change"
      );
      expect(lastCall[1].delta).toEqual({ start: 1, end: 1, text: "B" });
    });

    test("Calculates correct diff for Insertion in Middle", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      // Set initial state: "AC"
      fireEvent.change(textarea, { target: { value: "AC" } });
      mockSocket.emit.mockClear();

      // Change "AC" -> "ABC"
      fireEvent.change(textarea, { target: { value: "ABC" } });

      const lastCall = mockSocket.emit.mock.calls.find(
        (c) => c[0] === "text-change"
      );
      expect(lastCall[1].delta).toEqual({ start: 1, end: 1, text: "B" });
      // Insert 'B' at index 1. Old text end at 1 (nothing removed).
    });

    test("Calculates correct diff for Deletion", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      // Set "ABC"
      fireEvent.change(textarea, { target: { value: "ABC" } });
      mockSocket.emit.mockClear();

      // Change "ABC" -> "AC" (Delete B)
      fireEvent.change(textarea, { target: { value: "AC" } });

      const lastCall = mockSocket.emit.mock.calls.find(
        (c) => c[0] === "text-change"
      );
      expect(lastCall[1].delta).toEqual({ start: 1, end: 2, text: "" });
      // Remove index 1 to 2 (B), replace with empty.
    });

    test("Calculates correct diff for Replacement (Paste)", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      // Set "Hello World"
      fireEvent.change(textarea, { target: { value: "Hello World" } });
      mockSocket.emit.mockClear();

      // Change "Hello World" -> "Hello Jest World"
      fireEvent.change(textarea, { target: { value: "Hello Jest World" } });

      const lastCall = mockSocket.emit.mock.calls.find(
        (c) => c[0] === "text-change"
      );
      // Should detect insertion of "Jest " at index 6
      expect(lastCall[1].delta).toEqual({ start: 6, end: 6, text: "Jest " });
    });
  });

  describe("Zero Jitter Transformation (Remote Changes)", () => {
    test("Incoming insert BEFORE cursor shifts cursor forward", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      // 1. Local User types "World", cursor is at end (5)
      fireEvent.change(textarea, { target: { value: "World" } });
      textarea.setSelectionRange(5, 5); // Cursor after 'd'

      // 2. Remote User inserts "Hello " at start (0)
      triggerSocket("remote-change", {
        delta: { start: 0, end: 0, text: "Hello " },
      });

      // 3. Result: "Hello World", Cursor should be at 5 + 6 = 11
      expect(textarea.value).toBe("Hello World");
      expect(textarea.selectionStart).toBe(11);
      expect(textarea.selectionEnd).toBe(11);
    });

    test("Incoming insert AFTER cursor does NOT move cursor", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      // 1. Local User types "Hello", cursor at 5
      fireEvent.change(textarea, { target: { value: "Hello" } });
      textarea.setSelectionRange(5, 5);

      // 2. Remote User appends " World" at 5
      triggerSocket("remote-change", {
        delta: { start: 5, end: 5, text: " World" },
      });

      // 3. Cursor remains at 5
      expect(textarea.value).toBe("Hello World");
      expect(textarea.selectionStart).toBe(5);
    });

    test("Incoming deletion OVERLAPPING cursor collapses cursor", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      // 1. "Hello World". Cursor at 7 ('W').
      fireEvent.change(textarea, { target: { value: "Hello World" } });
      textarea.setSelectionRange(7, 7);

      // 2. Remote deletes "World" (index 6 to 11)
      triggerSocket("remote-change", {
        delta: { start: 6, end: 11, text: "" },
      });

      // 3. Result: "Hello ". Cursor was at 7, which is inside the deleted zone (6-11).
      // Logic dictates it should snap to the start of the change (6).
      expect(textarea.value).toBe("Hello ");
      expect(textarea.selectionStart).toBe(6);
    });
  });

  describe("Presence Rendering", () => {
    test("Renders remote cursor overlay", () => {
      const { container } = renderEditor();

      // Trigger remote cursor
      triggerSocket("remote-cursor", {
        id: "remote-1",
        username: "Bob",
        color: "#ff0000",
        selectionStart: 0,
        selectionEnd: 0,
      });

      // Look for the visual elements
      // Based on our implementation, the cursor is a span with specific styles or the tooltip
      const tooltip = screen.getByText("Bob");
      expect(tooltip).toBeInTheDocument();

      // Check color application (implementation detail, but necessary for visual test)
      // We look for the parent span of the tooltip or the tooltip itself having the color
      expect(tooltip).toHaveStyle({ backgroundColor: "#ff0000" });
    });
  });
});

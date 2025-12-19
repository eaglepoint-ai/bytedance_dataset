import { render, screen, fireEvent, act } from "@testing-library/react";
import LiveEditor from "@/client/LiveEditor";
import { socket } from "@/client/services/socket";

jest.mock("@/client/services/socket");

describe("LiveEditor Frontend Logic", () => {
  let callbacks = {};

  beforeEach(() => {
    callbacks = {};
    socket.on.mockImplementation((event, callback) => {
      callbacks[event] = callback;
    });
    socket.emit.mockClear();
  });

  const renderEditor = () =>
    render(<LiveEditor roomId="test-room" username="TestUser" />);


  test("Initialization: Joins room on mount", () => {
    renderEditor();
    expect(socket.emit).toHaveBeenCalledWith("join-room", {
      roomId: "test-room",
      username: "TestUser",
    });
  });

  describe("Handshake", () => {
    test("Responds to request-state with current content", () => {
      renderEditor();

      const textarea = screen.getByRole("textbox");
      fireEvent.change(textarea, { target: { value: "current state" } });

      act(() => {
        callbacks["request-state"]({ requesterId: "another-user" });
      });

      expect(socket.emit).toHaveBeenCalledWith("sync-state", {
        targetId: "another-user",
        content: "current state",
      });
    });
  });

  describe("Diff Algorithm (Local Changes)", () => {
    test("Calculates correct diff for Appending", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      fireEvent.change(textarea, { target: { value: "Hello" } });

      fireEvent.change(textarea, { target: { value: "Hello World" } });

      expect(socket.emit).toHaveBeenLastCalledWith("text-change", {
        roomId: "test-room",
        delta: {
          start: 5,
          end: 5,
          text: " World",
        },
      });
    });

    test("Calculates correct diff for Insertion in Middle", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      fireEvent.change(textarea, { target: { value: "Hlo" } });

      fireEvent.change(textarea, { target: { value: "Hello" } });

      expect(socket.emit).toHaveBeenLastCalledWith("text-change", {
        roomId: "test-room",
        delta: {
          start: 1,
          end: 1,
          text: "el",
        },
      });
    });

    test("Calculates correct diff for Deletion", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      fireEvent.change(textarea, { target: { value: "Hello World" } });

      fireEvent.change(textarea, { target: { value: "HelloWorld" } });

      expect(socket.emit).toHaveBeenLastCalledWith("text-change", {
        roomId: "test-room",
        delta: {
          start: 5,
          end: 6,
          text: "",
        },
      });
    });

    test("Calculates correct diff for Replacement (Paste)", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      fireEvent.change(textarea, { target: { value: "original text" } });

      fireEvent.change(textarea, {
        target: { value: "replacement text" },
      });

      expect(socket.emit).toHaveBeenLastCalledWith("text-change", {
        roomId: "test-room",
        delta: {
          start: 0,
          end: 8,
          text: "replacement",
        },
      });
    });
  });

  describe("Zero Jitter Transformation (Remote Changes)", () => {
    test("Incoming insert BEFORE cursor shifts cursor forward", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      fireEvent.change(textarea, {
        target: { value: "world", selectionStart: 5, selectionEnd: 5 },
      });

      act(() => {
        callbacks["remote-change"]({
          delta: { start: 0, end: 0, text: "Hello " },
        });
      });

      expect(textarea.value).toBe("Hello world");
      expect(textarea.selectionStart).toBe(5+6);
    });

    test("Incoming insert AFTER cursor does NOT move cursor", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      fireEvent.change(textarea, {
        target: { value: "Hello", selectionStart: 0, selectionEnd: 0 },
      });

      act(() => {
        callbacks["remote-change"]({
          delta: { start: 5, end: 5, text: " world" },
        });
      });

      expect(textarea.value).toBe("Hello world");
      expect(textarea.selectionStart).toBe(0);
    });

    test("Incoming deletion OVERLAPPING cursor collapses cursor", () => {
      renderEditor();
      const textarea = screen.getByRole("textbox");

      fireEvent.change(textarea, {
        target: {
          value: "one two three",
          selectionStart: 4,
          selectionEnd: 7,
        },
      });

      act(() => {
        callbacks["remote-change"]({
          delta: { start: 0, end: 7, text: "" },
        });
      });

      expect(textarea.value).toBe(" three");
      expect(textarea.selectionStart).toBe(0);
    });
  });

  describe("Presence Rendering", () => {
    test("Renders remote cursor overlay", async () => {
      renderEditor();

      act(() => {
        callbacks["user-joined"]({
          id: "user-2",
          username: "User Two",
          color: "#ff0000",
        });
      });

      act(() => {
        callbacks["remote-cursor"]({
          id: "user-2",
          selectionStart: 3,
          selectionEnd: 3,
          username: "User Two",
          color: "#ff0000",
        });
      });

      act(() => {
        callbacks["remote-change"]({
          delta: { start: 0, end: 0, text: "some text" },
        });
      });

      const cursorLabel = await screen.findByText("User Two");
      expect(cursorLabel).toBeInTheDocument();
      expect(cursorLabel.style.backgroundColor).toBe("rgb(255, 0, 0)");
    });
  });
});

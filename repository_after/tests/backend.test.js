const { createServer } = require("http");
const { Server } = require("socket.io");
const Client = require("socket.io-client");

// Note: In a real scenario, you would import your actual server app here.
// For this standalone test, we assume the server logic matches the provided spec.
// If you have your server exported in a module, import it.
// Otherwise, ensure your server is running on port 3001 before running these tests.

describe("Live Ephemeral Note Backend Protocol", () => {
  let clientSocketA, clientSocketB, clientSocketC;

  // Helper to wait for a socket event
  const waitFor = (socket, event) => {
    return new Promise((resolve) => {
      socket.once(event, resolve);
    });
  };

  beforeEach((done) => {
    // Connect new clients for each test to ensure clean state
    clientSocketA = new Client("http://localhost:3001");
    clientSocketB = new Client("http://localhost:3001");
    clientSocketC = new Client("http://localhost:3001");

    // meaningful delay to ensure connections
    setTimeout(done, 100);
  });

  afterEach(() => {
    clientSocketA.close();
    clientSocketB.close();
    clientSocketC.close();
  });

  test("Room Isolation: Clients in different rooms should not see each other", (done) => {
    clientSocketA.emit("join-room", { roomId: "room1", username: "UserA" });
    clientSocketC.emit("join-room", { roomId: "room2", username: "UserC" });

    // C should NOT receive notification that A joined
    clientSocketC.on("user-joined", () => {
      done(new Error("Leaked event across rooms"));
    });

    // Wait a bit to ensure silence
    setTimeout(() => done(), 500);
  });

  test("State Transfer Handshake: New user triggers state request flow", async () => {
    const roomId = "sync-room";

    // 1. User A joins and establishes 'truth'
    clientSocketA.emit("join-room", { roomId, username: "Host" });

    // 2. User B joins
    clientSocketB.emit("join-room", { roomId, username: "Guest" });

    // 3. Server should ask User A for state (because A was there first)
    const request = await waitFor(clientSocketA, "request-state");
    expect(request.requesterId).toBe(clientSocketB.id);

    // 4. User A sends state
    const docState = "Hello World";
    clientSocketA.emit("sync-state", {
      targetId: request.requesterId,
      content: docState,
    });

    // 5. User B should receive that state
    const response = await waitFor(clientSocketB, "receive-state");
    expect(response.content).toBe(docState);
  });

  test("Edit Broadcasting: Text changes are relayed to room members", (done) => {
    const roomId = "edit-room";
    clientSocketA.emit("join-room", { roomId, username: "A" });
    clientSocketB.emit("join-room", { roomId, username: "B" });

    const changeData = {
      roomId,
      delta: { start: 0, end: 0, text: "X" },
    };

    clientSocketB.on("remote-change", (data) => {
      try {
        expect(data.delta).toEqual(changeData.delta);
        expect(data.senderId).toBe(clientSocketA.id);
        done();
      } catch (e) {
        done(e);
      }
    });

    // Give time for join to process
    setTimeout(() => {
      clientSocketA.emit("text-change", changeData);
    }, 100);
  });

  test("Cursor Presence: Selections are relayed with user metadata", (done) => {
    const roomId = "cursor-room";
    const username = "CursorUser";

    clientSocketA.emit("join-room", { roomId, username });
    clientSocketB.emit("join-room", { roomId, username: "Observer" });

    clientSocketB.on("remote-cursor", (data) => {
      try {
        expect(data.id).toBe(clientSocketA.id);
        expect(data.username).toBe(username);
        expect(data.selectionStart).toBe(5);
        expect(data.selectionEnd).toBe(10);
        expect(data.color).toBeDefined(); // Server assigned color
        done();
      } catch (e) {
        done(e);
      }
    });

    setTimeout(() => {
      clientSocketA.emit("cursor-move", {
        roomId,
        selectionStart: 5,
        selectionEnd: 10,
      });
    }, 100);
  });
});

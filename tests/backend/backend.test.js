import { handleConnection } from "../../repository_after/server/services/socketHandlers";
import { initializeSocket, rooms, userMeta } from "../../repository_after/server/services/socket";
import { createServer } from "http";
import Client from "socket.io-client";

describe("Backend Tests", () => {
  let io, server, port;
  let clients = [];


  const createClient = () => {
    const client = new Client(`http://127.0.0.1:${port}`);
    clients.push(client);
    return new Promise((resolve) => {
      client.on("connect", () => resolve(client));
    });
  };


  const waitForEvent = (socket, event) => {
    return new Promise((resolve) => {
      socket.once(event, resolve);
    });
  };

  beforeAll((done) => {
    server = createServer();
    io = initializeSocket(server);
    handleConnection(io);
    server.listen(() => {
      port = server.address().port;
      done();
    });
  });

  afterEach(() => {
    clients.forEach((client) => client.close());
    clients = [];
    rooms.clear();
    userMeta.clear();
  });

  afterAll(() => {
    io.close();
    server.close();
  });

  test("User should join a room and be added to server state", async () => {
    const roomId = "test-room";
    const username = "test-user";
    const client = await createClient();

    client.emit("join-room", { roomId, username });

    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(rooms.has(roomId)).toBe(true);
    expect(rooms.get(roomId).size).toBe(1);
    expect(rooms.get(roomId).has(client.id)).toBe(true);
    expect(userMeta.has(client.id)).toBe(true);
    expect(userMeta.get(client.id).username).toBe(username);
  });

  test("User disconnect should remove them from rooms and metadata", async () => {
    const roomId = "disconnect-room";
    const username = "temp-user";
    const client = await createClient();

    client.emit("join-room", { roomId, username });
    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(rooms.get(roomId).has(client.id)).toBe(true);
    expect(userMeta.has(client.id)).toBe(true);

    client.close();
    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(rooms.has(roomId)).toBe(false);
    expect(userMeta.has(client.id)).toBe(false);
  });

  test("State Transfer Handshake: New user triggers state request flow", async () => {
    const roomId = "sync-room";
    const clientA = await createClient();

    clientA.emit("join-room", { roomId, username: "Host" });
    await new Promise((resolve) => setTimeout(resolve, 50));

    const clientB = await createClient();
    clientB.emit("join-room", { roomId, username: "Guest" });


    const request = await waitForEvent(clientA, "request-state");
    expect(request.requesterId).toBe(clientB.id);

    const docState = "Hello World from the Host";
    clientA.emit("sync-state", {
      targetId: request.requesterId,
      content: docState,
    });

    const response = await waitForEvent(clientB, "receive-state");
    expect(response.content).toBe(docState);
  });

  test("Edit Broadcasting: Text changes are relayed ONLY to room members", async () => {
    const roomA = "edit-room-A";
    const roomB = "edit-room-B";

    const clientA1 = await createClient();
    const clientA2 = await createClient();
    const clientB1 = await createClient();

    clientA1.emit("join-room", { roomId: roomA, username: "A1" });
    clientA2.emit("join-room", { roomId: roomA, username: "A2" });
    clientB1.emit("join-room", { roomId: roomB, username: "B1" });

    await new Promise((resolve) => setTimeout(resolve, 100));

    const changeData = {
      roomId: roomA,
      delta: { start: 0, end: 0, text: "X" },
    };

    let receivedByA2 = false;
    let receivedByB1 = false;

    clientA2.on("remote-change", (data) => {
      expect(data.delta).toEqual(changeData.delta);
      expect(data.senderId).toBe(clientA1.id);
      receivedByA2 = true;
    });

    clientB1.on("remote-change", () => {
      receivedByB1 = true;
    });

    clientA1.emit("text-change", changeData);

    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(receivedByA2).toBe(true);
    expect(receivedByB1).toBe(false);
  });

  test("Cursor Presence: Selections are relayed with user metadata", async () => {
    const roomId = "cursor-room";
    const username = "CursorUser";
    const clientA = await createClient();
    const clientB = await createClient();

    clientA.emit("join-room", { roomId, username });
    clientB.emit("join-room", { roomId, username: "Observer" });

    await new Promise((resolve) => setTimeout(resolve, 100));

    const cursorData = {
      roomId,
      selectionStart: 5,
      selectionEnd: 10,
    };

    const remoteCursorPromise = waitForEvent(clientB, "remote-cursor");
    clientA.emit("cursor-move", cursorData);

    const data = await remoteCursorPromise;
    expect(data.id).toBe(clientA.id);
    expect(data.username).toBe(username);
    expect(data.selectionStart).toBe(cursorData.selectionStart);
    expect(data.selectionEnd).toBe(cursorData.selectionEnd);
    expect(data.color).toBeDefined();
  });

  test("Last user leaving a room should delete the room", async () => {
    const roomId = "cleanup-room";
    const client1 = await createClient();
    const client2 = await createClient();

    client1.emit("join-room", { roomId, username: "User1" });
    client2.emit("join-room", { roomId, username: "User2" });
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(rooms.has(roomId)).toBe(true);
    expect(rooms.get(roomId).size).toBe(2);

    client1.close();
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(rooms.has(roomId)).toBe(true);
    expect(rooms.get(roomId).size).toBe(1);

    client2.close();
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(rooms.has(roomId)).toBe(false);
  });

  test("Joining an empty room should not trigger a state request", async () => {
    const roomId = "lonely-room";
    const client = await createClient();

    let stateRequested = false;
    client.on("request-state", () => {
      stateRequested = true;
    });

    client.emit("join-room", { roomId, username: "Solo" });
    await new Promise((resolve) => setTimeout(resolve, 50));

    expect(stateRequested).toBe(false);
    expect(rooms.has(roomId)).toBe(true);
    expect(rooms.get(roomId).size).toBe(1);
  });
});

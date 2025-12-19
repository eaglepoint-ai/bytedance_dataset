import { Server } from "socket.io";

const rooms = new Map();
const userMeta = new Map();

const initializeSocket = (server) => {
  const io = new Server(server, {
    cors: { origin: "*", methods: ["GET", "POST"] },
  });

  return io;
};

export { initializeSocket, rooms, userMeta };

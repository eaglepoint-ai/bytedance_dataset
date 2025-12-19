const { Server } = require("socket.io");

const rooms = new Map();
const userMeta = new Map();

const initializeSocket = (server) => {
  const io = new Server(server, {
    cors: { origin: "*", methods: ["GET", "POST"] },
  });

  return io;
};

module.exports = { initializeSocket, rooms, userMeta };

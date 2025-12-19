const { rooms, userMeta } = require("./socket");
const { getRandomColor } = require("../utils/color");

const handleConnection = (io) => {
  io.on("connection", (socket) => {
    console.log("User connected:", socket.id);

    socket.on("join-room", ({ roomId, username }) => {
      socket.join(roomId);

      const color = getRandomColor();
      userMeta.set(socket.id, { color, username });

      if (!rooms.has(roomId)) {
        rooms.set(roomId, new Set());
      }
      const roomSockets = rooms.get(roomId);

      if (roomSockets.size > 0) {
        const [firstClient] = roomSockets;
        io.to(firstClient).emit("request-state", { requesterId: socket.id });
      }

      roomSockets.add(socket.id);

      socket.to(roomId).emit("user-joined", {
        id: socket.id,
        color,
        username,
      });
    });

    socket.on("sync-state", ({ targetId, content }) => {
      io.to(targetId).emit("receive-state", { content });
    });

    socket.on("text-change", ({ roomId, delta }) => {
      socket.to(roomId).emit("remote-change", {
        senderId: socket.id,
        delta,
      });
    });

    socket.on("cursor-move", ({ roomId, selectionStart, selectionEnd }) => {
      socket.to(roomId).emit("remote-cursor", {
        id: socket.id,
        selectionStart,
        selectionEnd,
        ...userMeta.get(socket.id),
      });
    });

    socket.on("disconnecting", () => {
      const roomsJoined = [...socket.rooms];
      roomsJoined.forEach((roomId) => {
        if (rooms.has(roomId)) {
          rooms.get(roomId).delete(socket.id);
          if (rooms.get(roomId).size === 0) {
            rooms.delete(roomId);
          } else {
            socket.to(roomId).emit("user-left", { id: socket.id });
          }
        }
      });
      userMeta.delete(socket.id);
    });
  });
};

module.exports = { handleConnection };

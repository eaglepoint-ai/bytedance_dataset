const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors());

const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: "*", methods: ["GET", "POST"] }
});

// Map: RoomID -> Set of Socket IDs
const rooms = new Map();
// Map: SocketID -> { color, username }
const userMeta = new Map();

const getRandomColor = () => {
  const letters = '0123456789ABCDEF';
  let color = '#';
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
};

io.on('connection', (socket) => {
  console.log('User connected:', socket.id);

  socket.on('join-room', ({ roomId, username }) => {
    socket.join(roomId);
    
    // Assign color
    const color = getRandomColor();
    userMeta.set(socket.id, { color, username });

    // Handle Room Logic
    if (!rooms.has(roomId)) {
      rooms.set(roomId, new Set());
    }
    const roomSockets = rooms.get(roomId);
    
    // 1. Initial Sync: If room has others, ask one for the state
    if (roomSockets.size > 0) {
      const [firstClient] = roomSockets; // Pick the first available client
      io.to(firstClient).emit('request-state', { requesterId: socket.id });
    }

    roomSockets.add(socket.id);

    // Notify others of new user
    socket.to(roomId).emit('user-joined', { 
      id: socket.id, 
      color, 
      username 
    });
  });

  // 2. Relay State: Existing client sends state -> Server -> New Client
  socket.on('sync-state', ({ targetId, content }) => {
    io.to(targetId).emit('receive-state', { content });
  });

  // 3. Relay Edits (Text changes)
  socket.on('text-change', ({ roomId, delta, cursorPosition }) => {
    // Broadcast to everyone else in the room
    socket.to(roomId).emit('remote-change', { 
      senderId: socket.id, 
      delta, // { start, end, text, type }
    });
  });

  // 4. Relay Presence (Cursor moves/Selections)
  socket.on('cursor-move', ({ roomId, selectionStart, selectionEnd }) => {
    socket.to(roomId).emit('remote-cursor', {
      id: socket.id,
      selectionStart,
      selectionEnd,
      ...userMeta.get(socket.id)
    });
  });

  socket.on('disconnecting', () => {
    const roomsJoined = [...socket.rooms];
    roomsJoined.forEach((roomId) => {
      if (rooms.has(roomId)) {
        rooms.get(roomId).delete(socket.id);
        if (rooms.get(roomId).size === 0) {
          rooms.delete(roomId); // Room dies when last user leaves
        } else {
            socket.to(roomId).emit('user-left', { id: socket.id });
        }
      }
    });
    userMeta.delete(socket.id);
  });
});

server.listen(3001, () => {
  console.log('SERVER RUNNING ON 3001');
});
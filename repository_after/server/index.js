const { initializeExpress } = require("./services/express");
const { createServer } = require("./services/http");
const { initializeSocket } = require("./services/socket");
const { handleConnection } = require("./services/socketHandlers");

const app = initializeExpress();
const server = createServer(app);
const io = initializeSocket(server);

handleConnection(io);

server.listen(3001, () => {
  console.log("SERVER RUNNING ON 3001");
});

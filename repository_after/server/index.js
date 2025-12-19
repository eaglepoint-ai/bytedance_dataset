import { initializeExpress } from "./services/express.js";
import { createServer } from "./services/http.js";
import { initializeSocket } from "./services/socket.js";
import { handleConnection } from "./services/socketHandlers.js";

const app = initializeExpress();
const server = createServer(app);
const io = initializeSocket(server);

handleConnection(io);

server.listen(3000, () => {
  console.log("SERVER RUNNING ON 3000");
});

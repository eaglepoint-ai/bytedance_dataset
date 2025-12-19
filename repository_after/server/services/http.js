const http = require("http");

const createServer = (app) => {
  return http.createServer(app);
};

module.exports = { createServer };

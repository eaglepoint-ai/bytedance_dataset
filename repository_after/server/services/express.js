const express = require("express");
const cors = require("cors");

const initializeExpress = () => {
  const app = express();
  app.use(cors());
  return app;
};

module.exports = { initializeExpress };

import express from "express";
import cors from "cors";

export const initializeExpress = () => {
  const app = express();
  app.use(cors());
  return app;
};

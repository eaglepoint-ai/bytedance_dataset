import express from "express";
import cookieParser from "cookie-parser";
import cors from "cors";
import { env } from "./env.js";
import { initAuthSchema } from "./db.js";
import {
  register,
  login,
  logout,
  requireSession,
  session,
  seedConsultant,
  testSetRole,
  listConsultants,
} from "./auth.js";

async function main() {
  await initAuthSchema();

  const app = express();
  app.use(express.json());
  app.use(cookieParser());

  app.use(
    cors({
      origin: env.AUTH_CORS_ORIGIN,
      credentials: true,
    })
  );

  // Routes under /api/auth/*
  app.post("/api/auth/register", register);
  app.post("/api/auth/login", login);
  app.post("/api/auth/logout", logout);

  app.get("/api/auth/session", requireSession, session);
  app.get("/api/auth/consultants", listConsultants);

  // DEV ONLY
  app.post("/api/auth/seed-consultant", seedConsultant);
  app.post("/api/auth/test/set-role", testSetRole);

  app.get("/health", (_req, res) => res.json({ ok: true }));

  const port = Number(env.AUTH_PORT);
  app.listen(port, () => {
    console.log(`auth listening on :${port}`);
  });
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

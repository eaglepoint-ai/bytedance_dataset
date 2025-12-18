import { z } from "zod";

const EnvSchema = z.object({
  AUTH_PORT: z.string().default("3001"),
  DATABASE_URL: z.string(),
  AUTH_JWT_SECRET: z.string().default("dev-secret-change-me"),
  AUTH_COOKIE_NAME: z.string().default("ms_session"),
  AUTH_DEV_MODE: z.string().default("1"),
  AUTH_CORS_ORIGIN: z.string().default("http://localhost:5173"),
});

export const env = EnvSchema.parse({
  AUTH_PORT: process.env.AUTH_PORT,
  DATABASE_URL: process.env.DATABASE_URL,
  AUTH_JWT_SECRET: process.env.AUTH_JWT_SECRET,
  AUTH_COOKIE_NAME: process.env.AUTH_COOKIE_NAME,
  AUTH_DEV_MODE: process.env.AUTH_DEV_MODE,
  AUTH_CORS_ORIGIN: process.env.AUTH_CORS_ORIGIN,
});

export const isDevMode = env.AUTH_DEV_MODE === "1";

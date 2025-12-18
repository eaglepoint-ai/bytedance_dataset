import pg from "pg";
import { env } from "./env.js";

export const pool = new pg.Pool({
  connectionString: env.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://"),
});

export async function initAuthSchema(): Promise<void> {
  await pool.query(`
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
  `);
  await pool.query(`
    CREATE TABLE IF NOT EXISTS auth_users (
      id uuid PRIMARY KEY DEFAULT uuid_generate_v4(),
      email text NOT NULL UNIQUE,
      password_hash text NOT NULL,
      email_verified boolean NOT NULL DEFAULT false,
      role text NOT NULL DEFAULT 'user',
      created_at timestamptz NOT NULL DEFAULT now()
    );
  `);
}

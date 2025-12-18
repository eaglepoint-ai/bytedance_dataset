import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { z } from "zod";
import type { Request, Response, NextFunction } from "express";
import { env, isDevMode } from "./env.js";
import { pool } from "./db.js";
import type { Role, SessionUser } from "./types.js";

const RegisterSchema = z.object({
  email: z.string().email(),
  password: z.string().min(6),
  role: z.enum(["user", "consultant"]).default("user"),
});

const LoginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(1),
});

function signSession(user: SessionUser): string {
  return jwt.sign(user, env.AUTH_JWT_SECRET, { expiresIn: "7d" });
}

function setSessionCookie(res: Response, token: string) {
  // localhost + ports are same-site; allow cross-port requests with credentials
  res.cookie(env.AUTH_COOKIE_NAME, token, {
    httpOnly: true,
    secure: false, // local dev
    sameSite: "lax",
    path: "/",
    maxAge: 7 * 24 * 60 * 60 * 1000,
  });
}

function clearSessionCookie(res: Response) {
  res.clearCookie(env.AUTH_COOKIE_NAME, { path: "/" });
}

export async function register(req: Request, res: Response) {
  const parsed = RegisterSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "invalid_body" });

  const { email, password, role } = parsed.data;
  const password_hash = await bcrypt.hash(password, 10);

  try {
    const result = await pool.query(
      `INSERT INTO auth_users (email, password_hash, role)
       VALUES ($1,$2,$3)
       RETURNING id, email, role`,
      [email.toLowerCase(), password_hash, role]
    );

    const user = {
      id: result.rows[0].id,
      email: result.rows[0].email,
      role: result.rows[0].role as Role,
    } satisfies SessionUser;

    // Register does not log in by default; keep explicit.
    return res.status(201).json({ ok: true, user });
  } catch (e: any) {
    if (String(e?.code) === "23505") return res.status(409).json({ error: "email_taken" });
    return res.status(500).json({ error: "server_error" });
  }
}

export async function login(req: Request, res: Response) {
  const parsed = LoginSchema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "invalid_body" });

  const { email, password } = parsed.data;
  const result = await pool.query(
    `SELECT id, email, password_hash, role
     FROM auth_users
     WHERE email = $1`,
    [email.toLowerCase()]
  );
  if (result.rowCount === 0) return res.status(401).json({ error: "invalid_credentials" });

  const row = result.rows[0];
  const ok = await bcrypt.compare(password, row.password_hash);
  if (!ok) return res.status(401).json({ error: "invalid_credentials" });

  const user = {
    id: row.id,
    email: row.email,
    role: row.role as Role,
  } satisfies SessionUser;

  const token = signSession(user);
  setSessionCookie(res, token);
  return res.json({ ok: true, user });
}

export async function logout(_req: Request, res: Response) {
  clearSessionCookie(res);
  return res.json({ ok: true });
}

export function requireSession(req: Request, res: Response, next: NextFunction) {
  const token = req.cookies?.[env.AUTH_COOKIE_NAME] || (req.header("authorization")?.startsWith("Bearer ") ? req.header("authorization")!.slice(7) : null);
  if (!token) return res.status(401).json({ error: "unauthorized" });
  try {
    const decoded = jwt.verify(token, env.AUTH_JWT_SECRET) as SessionUser;
    (req as any).sessionUser = decoded;
    return next();
  } catch {
    return res.status(401).json({ error: "unauthorized" });
  }
}

export function session(req: Request, res: Response) {
  const user = (req as any).sessionUser as SessionUser | undefined;
  if (!user) return res.status(401).json({ error: "unauthorized" });
  return res.json({ user });
}

export async function seedConsultant(_req: Request, res: Response) {
  // DEV ONLY: create consultant@example.com if none exists
  if (!isDevMode) return res.status(404).json({ error: "not_found" });

  const email = "consultant@example.com";
  const password = "consultant123!";
  const password_hash = await bcrypt.hash(password, 10);
  const existing = await pool.query(`SELECT id FROM auth_users WHERE email=$1`, [email]);
  if ((existing.rows?.length ?? 0) > 0) {
    return res.json({ ok: true, email, password, existed: true });
  }
  const inserted = await pool.query(
    `INSERT INTO auth_users (email, password_hash, role)
     VALUES ($1,$2,'consultant')
     RETURNING id`,
    [email, password_hash]
  );
  return res.json({ ok: true, email, password, existed: false, id: inserted.rows[0].id });
}

export async function testSetRole(req: Request, res: Response) {
  if (!isDevMode) return res.status(404).json({ error: "not_found" });
  const schema = z.object({ email: z.string().email(), role: z.enum(["user","consultant"]) });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: "invalid_body" });

  const { email, role } = parsed.data;
  await pool.query(`UPDATE auth_users SET role=$2 WHERE email=$1`, [email.toLowerCase(), role]);
  return res.json({ ok: true });
}

export async function listConsultants(_req: Request, res: Response) {
  try {
    const result = await pool.query(
      `SELECT id, email FROM auth_users WHERE role = 'consultant' ORDER BY email`
    );
    return res.json(result.rows.map(row => ({ id: row.id, email: row.email })));
  } catch (e: any) {
    return res.status(500).json({ error: "server_error" });
  }
}

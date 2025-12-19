const AUTH_BASE_URL = import.meta.env.VITE_AUTH_BASE_URL || "http://localhost:3001";

export type SessionUser = {
  id: string;
  email: string;
  role: "user" | "consultant";
};

export async function authFetch(path: string, init: RequestInit = {}) {
  const res = await fetch(`${AUTH_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(init.headers || {}),
    },
  });
  const text = await res.text();
  let data: any = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!res.ok) {
    const err = new Error(data?.error || res.statusText);
    (err as any).status = res.status;
    (err as any).data = data;
    throw err;
  }
  return data;
}

export async function register(email: string, password: string, role: "user" | "consultant" = "user") {
  return authFetch("/api/auth/register", { method: "POST", body: JSON.stringify({ email, password, role }) });
}

export async function login(email: string, password: string) {
  return authFetch("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export async function logout() {
  return authFetch("/api/auth/logout", { method: "POST" });
}

export async function getSession(): Promise<{ user: SessionUser } | null> {
  try {
    return await authFetch("/api/auth/session", { method: "GET" });
  } catch (e: any) {
    if (e?.status === 401) return null;
    throw e;
  }
}

// DEV helpers (used by e2e)
export async function devSetRole(email: string, role: "user" | "consultant") {
  return authFetch("/api/auth/test/set-role", { method: "POST", body: JSON.stringify({ email, role }) });
}

export async function seedConsultant() {
  return authFetch("/api/auth/seed-consultant", { method: "POST" });
}

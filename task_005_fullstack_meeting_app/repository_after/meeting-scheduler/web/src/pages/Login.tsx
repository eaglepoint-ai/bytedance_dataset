import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login as doLogin } from "../lib/auth";

export default function Login() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  return (
    <div className="container">
      <div className="card">
        <h2>Login</h2>
        <div className="small">Sign in to manage bookings.</div>
        <div style={{ height: 16 }} />

        <label>Email</label>
        <input data-testid="login-email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />

        <div style={{ height: 10 }} />

        <label>Password</label>
        <input data-testid="login-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />

        {err && <div className="small" style={{ color: "#ffb4b4", marginTop: 8 }} data-testid="login-error">{err}</div>}

        <div style={{ height: 12 }} />
        <button
          className="btn"
          data-testid="login-submit"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setErr(null);
            try {
              const result = await doLogin(email, password);
              // Redirect based on role
              if (result?.user?.role === "consultant") {
                nav("/consultant");
              } else {
                nav("/slots");
              }
            } catch (e: any) {
              setErr(e?.message || "Failed");
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy ? "Signing in..." : "Sign in"}
        </button>

        <div style={{ height: 12 }} />
        <div className="small">
          No account? <Link to="/register">Register</Link>
        </div>
      </div>
    </div>
  );
}

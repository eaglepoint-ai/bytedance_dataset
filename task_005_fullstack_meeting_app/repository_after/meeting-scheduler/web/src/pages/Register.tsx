import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register as reg } from "../lib/auth";

export default function Register() {
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState<"user" | "consultant">("user");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  return (
    <div className="container">
      <div className="card">
        <h2>Register</h2>
        <div className="small">Create an account.</div>
        <div style={{ height: 16 }} />

        <label>Email</label>
        <input data-testid="register-email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" />

        <div style={{ height: 10 }} />

        <label>Password</label>
        <input data-testid="register-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Min 6 chars" />

        <div style={{ height: 10 }} />

        <label>Account Type</label>
        <select
          data-testid="register-role"
          value={role}
          onChange={(e) => setRole(e.target.value as "user" | "consultant")}
          style={{ width: "100%", padding: "8px", fontSize: "14px" }}
        >
          <option value="user">Normal User (Book consultations)</option>
          <option value="consultant">Consultant (Create slots & view bookings)</option>
        </select>

        {err && <div className="small" style={{ color: "#ffb4b4", marginTop: 8 }} data-testid="register-error">{err}</div>}

        <div style={{ height: 12 }} />
        <button
          className="btn"
          data-testid="register-submit"
          disabled={busy}
          onClick={async () => {
            setBusy(true);
            setErr(null);
            try {
              await reg(email, password, role);
              nav("/login");
            } catch (e: any) {
              setErr(e?.message || "Failed");
            } finally {
              setBusy(false);
            }
          }}
        >
          {busy ? "Creating..." : "Create account"}
        </button>

        <div style={{ height: 12 }} />
        <div className="small">
          Already have an account? <Link to="/login">Login</Link>
        </div>
      </div>
    </div>
  );
}

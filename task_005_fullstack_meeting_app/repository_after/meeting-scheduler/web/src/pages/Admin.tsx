import React, { useEffect, useState } from "react";
import { apiFetch } from "../api/client";

export default function Consultant() {
  const [items, setItems] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setBusy(true);
    setErr(null);
    try {
      const data = await apiFetch("/api/admin/meetings");
      setItems(data);
    } catch (e: any) {
      setErr(e?.message || "Failed");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div className="container">
      <div className="header">
        <div>
          <h2 style={{ margin: 0 }}>My Consultations</h2>
          <div className="small">View your booked consultations.</div>
        </div>
        <div className="row">
          <button className="btn secondary" onClick={load} disabled={busy} data-testid="consultant-refresh">
            {busy ? "Loading..." : "Refresh"}
          </button>
          <button
            className="btn secondary"
            data-testid="consultant-seed-slots"
            onClick={async () => {
              try {
                await apiFetch("/api/slots/seed", { method: "POST" });
                await load();
              } catch (e: any) {
                setErr(e?.message || "Failed to seed");
              }
            }}
          >
            Create Slots
          </button>
        </div>
      </div>

      {err && <div className="card" style={{ borderColor: "#b42318" }} data-testid="consultant-error">{err}</div>}

      <div className="card">
        <table className="table" data-testid="consultant-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Client</th>
              <th>Description</th>
              <th>Meet</th>
            </tr>
          </thead>
          <tbody>
            {items.map((m) => {
              const start = new Date(m.start_at);
              const end = new Date(m.end_at);
              const label = `${start.toLocaleString()} – ${end.toLocaleTimeString()}`;
              return (
                <tr key={m.id} data-testid={`consultant-row-${m.id}`}>
                  <td>{label}</td>
                  <td>{m.user_email}</td>
                  <td>{m.description}</td>
                  <td>
                    {m.google_meet_link ? (
                      <a href={m.google_meet_link} target="_blank" rel="noreferrer" data-testid={`consultant-link-${m.id}`}>
                        Join
                      </a>
                    ) : (
                      <span className="small">Pending</span>
                    )}
                  </td>
                </tr>
              );
            })}
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="small">No consultations booked yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

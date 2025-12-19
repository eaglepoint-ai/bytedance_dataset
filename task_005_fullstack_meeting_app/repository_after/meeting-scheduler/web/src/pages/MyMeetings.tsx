import React, { useEffect, useState } from "react";
import { apiFetch } from "../api/client";

export default function MyMeetings() {
  const [items, setItems] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function load() {
    setBusy(true);
    setErr(null);
    try {
      const data = await apiFetch("/api/meetings/me");
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
          <h2 style={{ margin: 0 }}>My Meetings</h2>
          <div className="small">Your booked and canceled meetings.</div>
        </div>
        <button className="btn secondary" onClick={load} disabled={busy} data-testid="refresh-my-meetings">
          {busy ? "Loading..." : "Refresh"}
        </button>
      </div>

      {err && <div className="card" style={{ borderColor: "#b42318" }} data-testid="mymeetings-error">{err}</div>}

      <div className="card">
        <table className="table" data-testid="mymeetings-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Status</th>
              <th>Meet</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {items.map((m) => {
              const start = new Date(m.start_at);
              const end = new Date(m.end_at);
              const label = `${start.toLocaleString()} – ${end.toLocaleTimeString()}`;
              return (
                <tr key={m.id} data-testid={`mymeeting-row-${m.id}`}>
                  <td>{label}</td>
                  <td><span className="badge">{m.status}</span></td>
                  <td>
                    {m.google_meet_link ? (
                      <a href={m.google_meet_link} target="_blank" rel="noreferrer" data-testid={`mymeeting-link-${m.id}`}>
                        Join
                      </a>
                    ) : (
                      <span className="small">Pending</span>
                    )}
                  </td>
                  <td>
                    {m.status === "BOOKED" ? (
                      <button
                        className="btn danger"
                        data-testid={`cancel-${m.id}`}
                        onClick={async () => {
                          await apiFetch(`/api/meetings/${m.id}/cancel`, { method: "POST" });
                          await load();
                        }}
                      >
                        Cancel
                      </button>
                    ) : (
                      <span className="small">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
            {items.length === 0 && (
              <tr>
                <td colSpan={4} className="small">No meetings yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

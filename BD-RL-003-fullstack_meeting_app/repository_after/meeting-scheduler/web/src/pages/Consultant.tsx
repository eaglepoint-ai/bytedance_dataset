import React, { useEffect, useState } from "react";
import { apiFetch } from "../api/client";

export default function Consultant() {
  const [items, setItems] = useState<any[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const [showCreateSlots, setShowCreateSlots] = useState(false);
  const [createBusy, setCreateBusy] = useState(false);
  const [createErr, setCreateErr] = useState<string | null>(null);
  
  // Create slots form state
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 1); // Tomorrow
    return d.toISOString().split("T")[0];
  });
  const [endDate, setEndDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 7); // 7 days from now
    return d.toISOString().split("T")[0];
  });
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");
  const [skipWeekends, setSkipWeekends] = useState(true);

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
            className="btn"
            data-testid="consultant-create-slots-btn"
            onClick={() => setShowCreateSlots(true)}
          >
            Create Slots
          </button>
        </div>
      </div>

      {err && <div className="card" style={{ borderColor: "#b42318" }} data-testid="consultant-error">{err}</div>}

      {showCreateSlots && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="header">
            <div>
              <h3 style={{ margin: 0 }}>Create Time Slots</h3>
              <div className="small">Create 30-minute slots for selected dates and hours</div>
            </div>
            <button className="btn secondary" onClick={() => setShowCreateSlots(false)}>
              Close
            </button>
          </div>
          
          <div style={{ marginTop: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
              <div>
                <label>Start Date</label>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  data-testid="create-slots-start-date"
                  style={{ width: "100%", padding: "8px" }}
                />
              </div>
              <div>
                <label>End Date</label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  data-testid="create-slots-end-date"
                  style={{ width: "100%", padding: "8px" }}
                />
              </div>
            </div>
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 12 }}>
              <div>
                <label>Start Time</label>
                <input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  data-testid="create-slots-start-time"
                  style={{ width: "100%", padding: "8px" }}
                />
              </div>
              <div>
                <label>End Time</label>
                <input
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  data-testid="create-slots-end-time"
                  style={{ width: "100%", padding: "8px" }}
                />
              </div>
            </div>
            
            <div style={{ marginBottom: 12 }}>
              <label style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <input
                  type="checkbox"
                  checked={skipWeekends}
                  onChange={(e) => setSkipWeekends(e.target.checked)}
                  data-testid="create-slots-skip-weekends"
                />
                Skip weekends (Saturday & Sunday)
              </label>
            </div>
            
            {createErr && (
              <div className="small" style={{ color: "#ffb4b4", marginBottom: 12 }} data-testid="create-slots-error">
                {createErr}
              </div>
            )}
            
            <div className="row" style={{ justifyContent: "flex-end" }}>
              <button
                className="btn"
                disabled={createBusy}
                data-testid="create-slots-submit"
                onClick={async () => {
                  setCreateBusy(true);
                  setCreateErr(null);
                  try {
                    const result = await apiFetch("/api/slots/create", {
                      method: "POST",
                      body: JSON.stringify({
                        start_date: startDate,
                        end_date: endDate,
                        start_time: startTime,
                        end_time: endTime,
                        skip_weekends: skipWeekends,
                      }),
                    });
                    setShowCreateSlots(false);
                    setErr(null);
                    await load();
                    alert(`Successfully created ${result.created} slots!`);
                  } catch (e: any) {
                    setCreateErr(e?.message || "Failed to create slots");
                  } finally {
                    setCreateBusy(false);
                  }
                }}
              >
                {createBusy ? "Creating..." : "Create Slots"}
              </button>
            </div>
          </div>
        </div>
      )}

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

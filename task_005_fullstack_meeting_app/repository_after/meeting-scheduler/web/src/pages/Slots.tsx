import React, { useEffect, useMemo, useState } from "react";
import { apiFetch } from "../api/client";
import { SlotList, type Slot } from "../components/SlotList";
import { BookingModal } from "../components/BookingModal";
import type { SessionUser } from "../lib/auth";

function toISO(d: Date) {
  return d.toISOString();
}

type Consultant = {
  id: string;
  email: string;
};

export default function Slots({ user }: { user: SessionUser }) {
  const [from, setFrom] = useState(() => {
    const d = new Date();
    d.setHours(0, 0, 0, 0);
    return d;
  });
  const [to, setTo] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() + 7);
    d.setHours(23, 59, 59, 999);
    return d;
  });

  const [consultants, setConsultants] = useState<Consultant[]>([]);
  const [selectedConsultantId, setSelectedConsultantId] = useState<string>("");
  const [slots, setSlots] = useState<Slot[]>([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const [selected, setSelected] = useState<Slot | null>(null);
  const [confirm, setConfirm] = useState<any | null>(null);

  const rangeLabel = useMemo(() => `${from.toLocaleDateString()} → ${to.toLocaleDateString()}`, [from, to]);

  async function loadConsultants() {
    try {
      const data = await apiFetch("/api/slots/consultants");
      if (Array.isArray(data)) {
        setConsultants(data);
        if (data.length > 0 && !selectedConsultantId) {
          setSelectedConsultantId(data[0].id);
        }
      }
    } catch (e: any) {
      console.error("Failed to load consultants", e);
      setErr(e?.message || "Failed to load consultants");
    }
  }

  async function load() {
    if (!selectedConsultantId) {
      setSlots([]);
      return;
    }
    setBusy(true);
    setErr(null);
    try {
      const data = await apiFetch(`/api/slots?from=${encodeURIComponent(toISO(from))}&to=${encodeURIComponent(toISO(to))}&consultant_id=${encodeURIComponent(selectedConsultantId)}`);
      setSlots(data);
    } catch (e: any) {
      setErr(e?.message || "Failed to load slots");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    loadConsultants();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedConsultantId, from, to]);

  return (
    <div className="container">
      <div className="header">
        <div>
          <h2 style={{ margin: 0 }}>Available Slots</h2>
          <div className="small" data-testid="slot-range">{rangeLabel}</div>
        </div>
        <button className="btn secondary" onClick={load} disabled={busy} data-testid="refresh-slots">
          {busy ? "Loading..." : "Refresh"}
        </button>
      </div>

      {consultants.length > 0 && (
        <div className="card" style={{ marginBottom: 16 }}>
          <label>Select Consultant</label>
          <select
            value={selectedConsultantId}
            onChange={(e) => setSelectedConsultantId(e.target.value)}
            data-testid="consultant-select"
            style={{ width: "100%", padding: "8px", fontSize: "14px", marginTop: "8px" }}
          >
            <option value="">-- Select a consultant --</option>
            {consultants.map((c) => (
              <option key={c.id} value={c.id}>
                {c.email}
              </option>
            ))}
          </select>
        </div>
      )}


      {err && <div className="card" style={{ borderColor: "#b42318" }} data-testid="slots-error">{err}</div>}

      <SlotList
        slots={slots}
        onBook={(s) => {
          setConfirm(null);
          setSelected(s);
        }}
      />

      <BookingModal
        open={!!selected}
        onClose={() => setSelected(null)}
        slotLabel={selected ? `${new Date(selected.start_at).toLocaleString()}` : ""}
        onConfirm={async (description) => {
          if (!selected) return;
          try {
            const res = await apiFetch("/api/meetings", {
              method: "POST",
              body: JSON.stringify({ slot_id: selected.id, description }),
            });
            setConfirm(res);
            setSelected(null);
            await load();
          } catch (e: any) {
            // Error will be shown in the modal
            throw e;
          }
        }}
      />

      {confirm && (
        <div className="card" style={{ marginTop: 12 }} data-testid="booking-confirm">
          <div style={{ fontWeight: 700 }}>Booking Confirmed</div>
          <div className="small">Status: <span className="badge">{confirm.status}</span></div>
          <div style={{ height: 8 }} />
          <div className="small">Meet link:</div>
          <div data-testid="meet-link">
            {confirm.google_meet_link ? (
              <a href={confirm.google_meet_link} target="_blank" rel="noreferrer">
                {confirm.google_meet_link}
              </a>
            ) : (
              <span className="small">Meet link pending / not configured ({confirm.meet_status})</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

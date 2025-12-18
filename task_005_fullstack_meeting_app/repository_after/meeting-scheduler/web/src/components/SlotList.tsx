import React from "react";

export type Slot = {
  id: string;
  start_at: string;
  end_at: string;
};

export function SlotList({
  slots,
  onBook,
}: {
  slots: Slot[];
  onBook: (slot: Slot) => void;
}) {
  if (slots.length === 0) {
    return <div className="card" data-testid="no-slots">No available slots in this range.</div>;
  }

  return (
    <div className="row" data-testid="slot-list">
      {slots.map((s) => {
        const start = new Date(s.start_at);
        const end = new Date(s.end_at);
        const label = `${start.toLocaleString()} – ${end.toLocaleTimeString()}`;

        return (
          <div key={s.id} className="card" style={{ flex: "1 1 280px" }} data-testid={`slot-card-${s.id}`}>
            <div style={{ fontWeight: 700 }} data-testid="slot-time">{label}</div>
            <div className="small">30 minutes</div>
            <div style={{ height: 10 }} />
            <button className="btn" onClick={() => onBook(s)} data-testid={`slot-book-${s.id}`}>
              Book
            </button>
          </div>
        );
      })}
    </div>
  );
}

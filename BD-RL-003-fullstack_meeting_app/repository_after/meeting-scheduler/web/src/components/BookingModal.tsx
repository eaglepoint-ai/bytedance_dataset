/// <reference path="../react-shim.d.ts" />
import React, { useState, useEffect } from "react";

export function BookingModal({
  open,
  onClose,
  onConfirm,
  slotLabel,
}: {
  open: boolean;
  onClose: () => void;
  onConfirm: (description: string) => Promise<void>;
  slotLabel: string;
}) {
  const [desc, setDesc] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  // Reset form when modal opens
  useEffect(() => {
    if (open) {
      setDesc("");
      setErr(null);
      setBusy(false);
    }
  }, [open]);

  if (!open) return null;

  const handleBackdropClick = (e: any) => {
    if (e.target === e.currentTarget && !busy) {
      onClose();
    }
  };

  const handleModalClick = (e: any) => {
    e.stopPropagation();
  };

  const handleSubmit = async () => {
    if (desc.trim().length === 0 || busy) return;
    
    setBusy(true);
    setErr(null);
    try {
      await onConfirm(desc.trim());
      // On success, close the modal (parent component will handle this)
      onClose();
    } catch (e: any) {
      setErr(e?.message || "Failed to book slot");
      setBusy(false);
    }
  };

  return (
    <div 
      className="modalBackdrop" 
      data-testid="book-modal-backdrop"
      onClick={handleBackdropClick}
    >
      <div className="card modal" data-testid="book-modal" onClick={handleModalClick}>
        <div className="header">
          <div>
            <div style={{ fontWeight: 700 }}>Book Slot</div>
            <div className="small" data-testid="book-slot-label">{slotLabel}</div>
          </div>
          <button 
            className="btn secondary" 
            onClick={onClose} 
            disabled={busy} 
            data-testid="book-modal-close"
          >
            Close
          </button>
        </div>

        <label>Description</label>
        <textarea
          data-testid="book-description"
          rows={4}
          placeholder="What do you want to discuss?"
          value={desc}
          onChange={(e: any) => setDesc(e.target.value)}
          disabled={busy}
        />
        {err && (
          <div className="small" style={{ color: "#ffb4b4", marginTop: 8 }} data-testid="book-error">
            {err}
          </div>
        )}

        <div className="row" style={{ justifyContent: "flex-end", marginTop: 10 }}>
          <button
            className="btn"
            disabled={busy || desc.trim().length === 0}
            data-testid="book-confirm"
            onClick={handleSubmit}
          >
            {busy ? "Booking..." : "Confirm Booking"}
          </button>
        </div>
      </div>
    </div>
  );
}

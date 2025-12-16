import re

def normalize_id(raw: str) -> str:
    # Accepts: " abc-123 ", "ABC_123", "Abc 123"
    # Current behavior:
    # - strip ends
    # - uppercase
    # - any run of non-alnum becomes a single "-"
    # - keep leading/trailing "-" if produced
    s = (raw or "").strip().upper()
    s = re.sub(r"[^A-Z0-9]+", "-", s)
    return s
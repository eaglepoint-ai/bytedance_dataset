import re


def _normalize_temp(s: str) -> str:
    # Preserve underscores. Convert every other non-alnum char to "-".
    out = []
    for ch in s:
        if "A" <= ch <= "Z" or "0" <= ch <= "9" or ch == "_":
            out.append(ch)
        else:
            out.append("-")
    return "".join(out)


def normalize_id(raw: str) -> str:
    # Accepts: " abc-123 ", "ABC_123", "Abc 123"
    # Current behavior:
    # - strip ends
    # - uppercase
    # - any run of non-alnum becomes a single "-"
    # - keep leading/trailing "-" if produced
    s = (raw or "").strip().upper()

    # TEMP-only behavior: keep "_" as "_" and normalize other non-alnum to "-"
    if s.startswith("TEMP"):
        return _normalize_temp(s)

    # Non-TEMP behavior must remain byte-for-byte identical to historical output
    s = re.sub(r"[^A-Z0-9]+", "-", s)
    return s
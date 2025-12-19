import re

def format_ids(ids):
    """
    Input:
      ids: list of strings or None
    """
    out = []
    for x in ids:
        if x is None:
            continue
        s = x.strip().upper()
        s = re.sub(r"[^A-Z0-9]+", "-", s)
        out.append(s)
    return out
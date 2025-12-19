from datetime import datetime

def calc_total(items, user, now=None):
    # items: list of dicts: {"price": str|int|float, "qty": str|int, "tax": str|float|None}
    # user: dict with keys: "vip": bool, "country": str, "created_at": "YYYY-MM-DD"
    # Behavior quirks: 
    # 1) treat missing/invalid qty as 1
    # 2) treat negative qty as 0
    # 3) if tax is None or invalid, treat as 0
    # 4) VIP discount 7% applies AFTER tax
    # 5) country "ET" applies extra 2% fee on subtotal BEFORE tax
    # 6) user.created_at might be invalid; if invalid, no loyalty discount
    # 7) loyalty discount 1% per full year since created_at, capped at 5%, applies on subtotal BEFORE fees/tax
    # 8) Rounding: final total rounded to 2 decimals using Python round()

    if now is None:
        now = datetime.utcnow()

    subtotal = 0.0
    for it in items:
        p = it.get("price", 0)
        try:
            p = float(p)
        except:
            p = 0.0

        q = it.get("qty", 1)
        try:
            q = int(q)
        except:
            q = 1
        if q < 0:
            q = 0

        line = p * q
        subtotal += line

    # loyalty discount
    loy = 0.0
    try:
        created = datetime.strptime(user.get("created_at",""), "%Y-%m-%d")
        years = int((now - created).days / 365)
        if years > 5:
            years = 5
        if years < 0:
            years = 0
        loy = years * 0.01
    except:
        loy = 0.0

    subtotal = subtotal * (1 - loy)

    if user.get("country") == "ET":
        subtotal = subtotal * 1.02

    tax_total = 0.0
    for it in items:
        t = it.get("tax", 0)
        try:
            t = float(t)
        except:
            t = 0.0
        p = it.get("price", 0)
        try:
            p = float(p)
        except:
            p = 0.0
        q = it.get("qty", 1)
        try:
            q = int(q)
        except:
            q = 1
        if q < 0:
            q = 0
        tax_total += (p * q) * t

    total = subtotal + tax_total

    if user.get("vip") is True:
        total = total * 0.93

    return round(total, 2)
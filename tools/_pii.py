"""PII guard: mask personal data in query results BEFORE an AI agent sees them.

Two layers:
  1. Column names that identify a person (names, phone, Aadhaar, DOB, address, GPS, IDs, staff names).
  2. Cell values that look like a phone number, Aadhaar number or email address, in ANY column.
Aggregates (counts per village etc.) pass through untouched. Masking is always on in these tools.
"""
import re

PII_COLUMN = re.compile(
    r"(^|[^a-z])("
    r"first[ _]?name|last[ _]?name|middle[ _]?name|full[ _]?name|^name$|"
    r"(child|mother|father|husband|wife|spouse|guardian|beneficiary|member|student|participant|patient|person|"
    r"respondent|caregiver|head|woman|women|girl|boy|parent|son|daughter|worker|facilitator|teacher|staff|user|"
    r"asha|anm|aww|volunteer)[^a-z]*('?s)?[^a-z]*name|"
    r"name[^a-z]*of[^a-z]*(the[^a-z]*)?(child|mother|father|husband|guardian|beneficiary|member|student|person)|"
    r"username|phone|mobile|contact|whatsapp|aadha+r|aadhar|uid[^a-z]|email|e-mail|"
    r"dob|date[ _]?of[ _]?birth|birth[ _]?date|"
    r"address[^a-z]*line|house[ _]?(no|number|name)|landmark|pin[ _]?code|postal|"
    r"gps|latitude|longitude|lat[^a-z]|lng|location[ _]?coord|coordinates|"
    r"abha|ration[ _]?card|bank|ifsc|account[ _]?(no|number)|pan[ _]?(no|number|card)|voter|passport|"
    r"identity[ _]?(no|number|proof)|id[ _]?proof"
    r")", re.I)

# Location-level names are NOT personal ("Village name", "Block name"); never mask these.
NOT_PII = re.compile(r"(village|block|district|state|cluster|para|sector|awc|school|phc|sub ?cent|centre|center|"
                     r"project|program|programme|encounter|subject|form|concept|table|column|org|organisation|"
                     r"cohort|class|batch|group|donor|type|status|category|dashboard|card|collection)[^a-z]*name", re.I)

PII_VALUE = [
    re.compile(r"(?<!\d)(\+?91[\s-]?)?[6-9]\d{9}(?!\d)"),         # Indian mobile
    re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)"),       # Aadhaar-shaped
    re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"),  # email
]
MASK = "•••"


def is_pii_column(name):
    n = str(name)
    return bool(PII_COLUMN.search(n)) and not NOT_PII.search(n)


def mask_rows(cols, rows):
    """Return (masked_rows, masked_column_names, value_hits)."""
    pii_idx = {i for i, c in enumerate(cols) if is_pii_column(c)}
    hits = 0
    out = []
    for row in rows:
        new = []
        for i, v in enumerate(row):
            if v is None or v == "":
                new.append(v)
            elif i in pii_idx:
                new.append(MASK)
            else:
                s = str(v)
                for rx in PII_VALUE:
                    s, n = rx.subn(MASK, s)
                    hits += n
                new.append(s if s != str(v) else v)
        out.append(new)
    return out, [cols[i] for i in sorted(pii_idx)], hits


def print_table(cols, rows, limit=50, out=None):
    import sys
    out = out or sys.stdout
    masked, pcols, hits = mask_rows(cols, rows[:limit])
    print("\t".join(str(c) for c in cols), file=out)
    for r in masked:
        print("\t".join("" if v is None else str(v) for v in r), file=out)
    note = f"-- {len(rows)} row(s)" + (f", showing {limit}" if len(rows) > limit else "")
    if pcols or hits:
        note += f" · PII masked: columns {pcols or '-'}; {hits} value(s) in other columns"
    print(note, file=sys.stderr)

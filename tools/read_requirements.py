#!/usr/bin/env python3
"""Turn a client's requirement sheet into one clean markdown file an agent can read.

  python3 tools/read_requirements.py <file.xlsx | file.csv | Google Sheet link> [--org <schema>] [--name <label>]

Accepts:
  • Excel .xlsx  — every tab
  • .csv         — one table
  • Google Sheet link — every tab. The sheet must be shared "Anyone with the link can view";
    otherwise download it (File → Download → .xlsx) and pass the file.
Writes requirements/<org>/<name>.md (gitignored — client documents stay local) and prints the path.
Standard library only. Personal data in cells (names, phones, Aadhaar, emails…) is masked.
"""
import argparse, csv, datetime, io, os, re, sys, urllib.request, zipfile
import xml.etree.ElementTree as ET
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _pii import mask_rows

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
MAX_ROWS = 400


# ---------- readers ----------
def col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def read_xlsx(data):
    """Minimal .xlsx reader (values only) → [(sheet_name, rows)]."""
    z = zipfile.ZipFile(io.BytesIO(data))
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", NS):
            shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['m']}}}t")))
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    target = {r.get("Id"): r.get("Target") for r in rels}
    out = []
    for sh in wb.find("m:sheets", NS):
        name = sh.get("name")
        path = target[sh.get(f"{{{NS['r']}}}id")].lstrip("/")
        path = path if path.startswith("xl/") else "xl/" + path
        root = ET.fromstring(z.read(path))
        rows = []
        for r in root.iter(f"{{{NS['m']}}}row"):
            row = {}
            for c in r.findall("m:c", NS):
                t, v = c.get("t"), c.find("m:v", NS)
                if t == "s" and v is not None:
                    val = shared[int(v.text)]
                elif t == "inlineStr":
                    val = "".join(x.text or "" for x in c.iter(f"{{{NS['m']}}}t"))
                elif t == "b" and v is not None:
                    val = "TRUE" if v.text == "1" else "FALSE"
                else:
                    val = v.text if v is not None else ""
                row[col_index(c.get("r"))] = (val or "").strip()
            if row:
                width = max(row) + 1
                rows.append([row.get(i, "") for i in range(width)])
        out.append((name, rows))
    return out


def read_csv(data):
    text = data.decode("utf-8-sig", "replace")
    return [("Sheet1", [[c.strip() for c in r] for r in csv.reader(io.StringIO(text))])]


def fetch_google(url):
    m = re.search(r"/spreadsheets/d/([A-Za-z0-9_-]+)", url)
    if not m:
        sys.exit("Not a Google Sheets link (expected …/spreadsheets/d/<id>/…).")
    export = f"https://docs.google.com/spreadsheets/d/{m.group(1)}/export?format=xlsx"
    try:
        with urllib.request.urlopen(export, timeout=60) as r:
            data, ctype = r.read(), r.headers.get("Content-Type", "")
    except Exception as e:
        sys.exit(f"Couldn't download the sheet ({e}).\n" + PRIVATE_HELP)
    if not data.startswith(b"PK"):          # got an HTML login page instead of an xlsx
        sys.exit("The sheet isn't publicly readable.\n" + PRIVATE_HELP)
    return data


PRIVATE_HELP = ("Either: share it as 'Anyone with the link → Viewer', or download it "
                "(File → Download → Microsoft Excel .xlsx) and pass the file path instead.")


# ---------- cleaning ----------
def clean(rows):
    rows = [r for r in rows if any(c for c in r)]                     # drop empty rows
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    keep = [i for i in range(width) if any(r[i] for r in rows)]       # drop empty columns
    rows = [[r[i] for i in keep] for r in rows]
    # header = first row with ≥2 non-empty cells
    h = next((i for i, r in enumerate(rows) if sum(1 for c in r if c) >= 2), 0)
    title_rows = [" ".join(c for c in r if c) for r in rows[:h]]
    header = [c or f"Column {i+1}" for i, c in enumerate(rows[h])]
    body = rows[h + 1:]
    # carry down merged-looking blanks in the FIRST column (section/indicator groups)
    last = ""
    for r in body:
        if r[0]:
            last = r[0]
        elif any(r[1:]):
            r[0] = last
    return title_rows, header, body


def md_cell(v):
    return str(v).replace("|", "\\|").replace("\r", "").replace("\n", "<br>")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="path to .xlsx/.csv, or a Google Sheets link")
    ap.add_argument("--org", default="unsorted", help="org schema, e.g. sangwari (used for the output folder)")
    ap.add_argument("--name", default=None, help="label for the output file")
    a = ap.parse_args()

    src = a.source
    if src.startswith("http"):
        sheets, label = read_xlsx(fetch_google(src)), "google-sheet"
    else:
        data = open(os.path.expanduser(src), "rb").read()
        label = os.path.splitext(os.path.basename(src))[0]
        if data.startswith(b"PK"):
            sheets = read_xlsx(data)
        elif src.lower().endswith((".xls",)):
            sys.exit("Old .xls format: open it and 'Save as' .xlsx (or export CSV), then try again.")
        else:
            sheets = read_csv(data)

    name = re.sub(r"[^A-Za-z0-9_-]+", "-", a.name or label).strip("-").lower() or "requirements"
    org = re.sub(r"[^a-z0-9_]+", "_", a.org.lower())
    out_dir = os.path.join(ROOT, "requirements", org)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{name}.md")

    lines = [f"# Requirements — {name}", "",
             f"Source: `{'Google Sheet' if src.startswith('http') else os.path.basename(src)}` · "
             f"read {datetime.date.today()} · org: `{org}`", "",
             "> Next: map every row to data using `schemas/<org>/CATALOG.md` and fill "
             "`templates/requirement-mapping.md` (buildable / needs clarification / not in data) before building.", ""]
    summary, masked_total = [], 0
    for sheet, raw in sheets:
        cleaned = clean(raw)
        if not cleaned or not cleaned[2]:
            continue
        titles, header, body = cleaned
        body, pcols, hits = mask_rows(header, body, bare_name_needs_context=True)
        masked_total += hits + (len(body) * len(pcols))
        truncated = len(body) > MAX_ROWS
        body = body[:MAX_ROWS]
        lines += [f"## Tab: {sheet}  ({len(body)} rows)", ""]
        lines += [f"_{t}_" for t in titles if t] + ([""] if titles else [])
        lines.append("| # | " + " | ".join(md_cell(h) for h in header) + " |")
        lines.append("|---|" + "---|" * len(header))
        for i, r in enumerate(body, 1):
            lines.append(f"| {i} | " + " | ".join(md_cell(v) for v in r) + " |")
        if truncated:
            lines.append(f"\n_(showing first {MAX_ROWS} rows — this looks like data, not requirements)_")
        if pcols:
            lines.append(f"\n_Personal-data columns masked: {', '.join(pcols)}_")
        lines.append("")
        summary.append(f"{sheet}: {len(body)} rows × {len(header)} cols")
    if not summary:
        sys.exit("No tables found in the sheet.")
    open(out_path, "w").write("\n".join(lines))
    print(f"✓ {os.path.relpath(out_path, ROOT)}")
    for s in summary:
        print("  ·", s)
    if masked_total:
        print(f"  · {masked_total} personal-data value(s) masked")


if __name__ == "__main__":
    main()

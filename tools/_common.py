"""Shared helpers for tools/*.py — env loading, HTTP with retry, backups, diffs. Standard library only."""
import datetime, difflib, json, os, re, sys, time, urllib.error, urllib.request, http.cookiejar

TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS)
BACKUPS = os.path.join(ROOT, "backups")


def load_env():
    env = {}
    path = os.path.join(TOOLS, ".env")
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if k in env or k.startswith(("METABASE_", "SUPERSET_"))})
    return env


def die(msg, code=1):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


class Http:
    """Tiny JSON client with retry/backoff and an optional cookie jar."""

    def __init__(self, base, headers=None, cookies=False, timeout=120):
        self.base, self.headers, self.timeout = base.rstrip("/"), dict(headers or {}), timeout
        handlers = [urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar())] if cookies else []
        self.opener = urllib.request.build_opener(*handlers)

    def call(self, method, path, body=None, headers=None, raw=False):
        data = json.dumps(body).encode() if body is not None else None
        h = {"Content-Type": "application/json", **self.headers, **(headers or {})}
        for attempt in range(4):
            req = urllib.request.Request(self.base + path, data=data, method=method, headers=h)
            try:
                with self.opener.open(req, timeout=self.timeout) as r:
                    txt = r.read().decode("utf-8", "replace")
                    return txt if raw else (json.loads(txt) if txt else {})
            except urllib.error.HTTPError as e:
                if e.code in (429, 502, 503, 504) and attempt < 3:
                    time.sleep(2 ** attempt * 2); continue
                die(f"{method} {path} → HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:600]}")
            except urllib.error.URLError as e:
                if attempt < 3:
                    time.sleep(2 ** attempt * 2); continue
                die(f"{method} {path} → {e}")

    get = lambda self, p, **k: self.call("GET", p, **k)
    post = lambda self, p, b=None, **k: self.call("POST", p, b, **k)
    put = lambda self, p, b=None, **k: self.call("PUT", p, b, **k)


def backup(kind, oid, obj):
    os.makedirs(BACKUPS, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(BACKUPS, f"{kind}_{oid}_{ts}.json")
    with open(path, "w") as f:
        json.dump(obj, f, indent=2, default=str)
    return path


def show_diff(old, new, label="sql"):
    """Print a unified diff, ignoring trailing whitespace. Returns True if there is a real change."""
    a = [l.rstrip() + "\n" for l in old.strip().splitlines()]
    b = [l.rstrip() + "\n" for l in new.strip().splitlines()]
    d = "".join(difflib.unified_diff(a, b, f"{label} (live)", f"{label} (new)"))
    print(d or "(no change — the new SQL is the same as the live SQL)")
    return bool(d)


def strip_optional(sql):
    """Remove Metabase [[ ... ]] optional blocks (multi-line) — how the card runs with no filters set."""
    return re.sub(r"\[\[.*?\]\]", "", sql, flags=re.S)


def template_vars(sql):
    seen = []
    for v in re.findall(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}", sql):
        if v not in seen:
            seen.append(v)
    return seen

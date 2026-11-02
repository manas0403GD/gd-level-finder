import json, sqlite3, gzip, urllib.request, urllib.error, re, time
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory, Response

ROOT = Path(__file__).parent
DB = ROOT / "gdlf.sqlite3"
# GDDL tier values are bundled locally; they do not depend on AREDL.
try:
    _gddl_rows = json.loads((ROOT / "levels.json").read_text(encoding="utf-8"))
    GDDL_TIERS = {str(v.get("id")): v.get("tier") for v in _gddl_rows}
    GDDL_SIDE_TIERS = {str(v.get("id")): v.get("sideTier") for v in _gddl_rows}
except Exception:
    GDDL_TIERS, GDDL_SIDE_TIERS = {}, {}

app = Flask(__name__, static_folder="static")

@app.after_request
def disable_browser_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

def db():
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    return c


def ensure_ideas_table():
    with db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS community_ideas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            author TEXT NOT NULL DEFAULT 'Anonymous',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""")

ensure_ideas_table()

def json_response(data):
    raw = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    packed = gzip.compress(raw, compresslevel=6)
    return Response(packed, content_type="application/json; charset=utf-8",
                    headers={"Content-Encoding": "gzip", "Vary": "Accept-Encoding"})


_LIST_CACHE = {"time": 0, "data": None}
def _fetch_json(url, extra_headers=None):
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    }
    if "aredl.net" in url:
        headers.update({"Origin": "https://aredl.net", "Referer": "https://aredl.net/"})
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=22) as response:
        return json.loads(response.read().decode("utf-8")), response.headers


def _fetch_aredl_levels(list_type="aredl"):
    """Fetch the current public AREDL classic list."""
    if list_type != "aredl":
        raise ValueError("Unknown AREDL list type")
    base = "https://api.aredl.net/v2/api/aredl/levels"
    url = base + "?exclude_legacy=false&exclude_pending=false&exclude_removed=false"
    payload, headers = _fetch_json(url, {
        "Origin": "https://aredl.net",
        "Referer": "https://aredl.net/",
        "Accept": "application/json",
    })
    rows = [v for v in _extract_array(payload)
            if isinstance(v, dict) and v.get("level_id") is not None]
    if not rows:
        raise RuntimeError(url + ": response contained no recognizable level records")
    return rows, headers

def _extract_array(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "levels", "demons", "results", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    return []

@app.get("/api/list-data")
def list_data():
    # Cache public list snapshots for 30 minutes; this endpoint also avoids browser CORS restrictions.
    if (_LIST_CACHE["data"] is not None and not _LIST_CACHE["data"].get("errors")
            and time.time() - _LIST_CACHE["time"] < 1800):
        return jsonify(_LIST_CACHE["data"])
    result = {"pointercrate": [], "aredl": [], "errors": {}}
    # Pointercrate documents the listed endpoint with limit/after pagination (max 100).
    try:
        after = None
        for _ in range(3):  # top 300 currently ranked demons is sufficient for this database filter
            url = "https://pointercrate.com/api/v2/demons/listed/?limit=100"
            if after is not None:
                url += "&after=" + str(after)
            page, _headers = _fetch_json(url)
            rows = _extract_array(page)
            if not rows:
                break
            result["pointercrate"].extend(
                [v for v in rows if isinstance(v, dict) and v.get("level_id") is not None]
            )
            positions = [v.get("position") for v in rows if isinstance(v, dict) and v.get("position") is not None]
            if len(rows) < 100 or not positions:
                break
            after = max(positions)
    except Exception as exc:
        result["errors"]["pointercrate"] = str(exc)
    try:
        result["aredl"], _ = _fetch_aredl_levels()
    except Exception as exc:
        result["errors"]["aredl"] = str(exc)
    # Cache only a complete snapshot. If any upstream is blocked, retry next time
    # rather than caching an incomplete list-filter dataset for 30 minutes.
    if not result["errors"] and (result["pointercrate"] or result["aredl"]):
        _LIST_CACHE["data"] = result
        _LIST_CACHE["time"] = time.time()
    return jsonify(result)

@app.get("/")
def home():
    return send_from_directory(ROOT / "static", "index.html")

@app.get("/api/ideas")
def get_ideas():
    page = max(1, request.args.get("page", 1, type=int))
    per_page = min(20, max(1, request.args.get("per_page", 8, type=int)))
    with db() as c:
        total = c.execute("SELECT COUNT(*) FROM community_ideas").fetchone()[0]
        rows = c.execute(
            "SELECT id,title,description,author,created_at FROM community_ideas ORDER BY id DESC LIMIT ? OFFSET ?",
            (per_page, (page - 1) * per_page)
        ).fetchall()
    return jsonify(items=[dict(row) for row in rows], page=page, per_page=per_page, total=total, pages=max(1, (total + per_page - 1) // per_page))


@app.post("/api/ideas")
def submit_idea():
    data = request.get_json(silent=True) or {}
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()
    author = str(data.get("author", "")).strip() or "Anonymous"
    if not title or not description:
        return jsonify(error="Please add both a title and a description."), 400
    if len(title) > 90 or len(description) > 1200 or len(author) > 35:
        return jsonify(error="Please shorten your idea or display name."), 400
    if len(title) < 4 or len(description) < 10:
        return jsonify(error="Please provide a little more detail."), 400
    with db() as c:
        cur = c.execute("INSERT INTO community_ideas(title,description,author) VALUES(?,?,?)", (title, description, author))
        idea_id = cur.lastrowid
        row = c.execute("SELECT id,title,description,author,created_at FROM community_ideas WHERE id=?", (idea_id,)).fetchone()
    return jsonify(dict(row)), 201


@app.get("/api/status")
def status():
    with db() as c:
        total = c.execute("SELECT COUNT(*) FROM levels").fetchone()[0]
        cached = c.execute("SELECT COUNT(*) FROM tag_cache").fetchone()[0]
        nonempty = c.execute("SELECT COUNT(*) FROM tag_cache WHERE tags_json NOT IN ('[]','')").fetchone()[0]
    return jsonify(levels=total, cached=cached, withTags=nonempty, empty=total-nonempty, preloaded=True)

@app.get("/api/levels")
def levels():
    q = request.args.get("q", "").strip()
    with db() as c:
        rows = c.execute("""SELECT l.id,l.name,l.creator,l.song,l.difficulty,l.rating,l.side_rating,
            l.enjoyment_avg,l.enjoyment_votes,
            COALESCE(NULLIF(t.tags_json,''),NULLIF(l.tags_json,''),'[]') AS tags_json
            FROM levels l LEFT JOIN tag_cache t ON t.level_id=l.id
            WHERE (?='' OR l.name LIKE ? OR l.creator LIKE ? OR l.song LIKE ? OR l.id LIKE ?)
            ORDER BY l.name COLLATE NOCASE""",
            (q, f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    output = []
    for row in rows:
        item = dict(row)
        item["tier"] = GDDL_TIERS.get(str(item["id"]))
        item["side_tier"] = GDDL_SIDE_TIERS.get(str(item["id"]))
        output.append(item)
    return json_response(output)

if __name__ == "__main__":
    if not DB.exists():
        raise SystemExit("gdlf.sqlite3 is missing. Keep it beside server.py.")
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)

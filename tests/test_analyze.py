import json, os, re, pathlib, pytest, requests

BASE = os.getenv("BASE_URL", "http://localhost:8000")
CASES = json.loads((pathlib.Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
KEYS = ["detected_language","summary","possible_patterns","red_flags","urgency",
        "suggested_specialist","questions_for_doctor","what_to_track","disclaimer"]
BAD = [r"\byou (definitely |probably )?(have|are suffering from)\b.*pcos",
       r"\byou have pcos", r"\d+\s?(mg|mcg)\b", r"metformin", r"\bspironolactone\b"]
SCRIPT = {"kn": r"[\u0C80-\u0CFF]", "hi": r"[\u0900-\u097F]"}

@pytest.mark.parametrize("c", CASES, ids=lambda c: f"case{c['id']}")
def test_case(c):
    r = requests.post(f"{BASE}/analyze", json={"text": c["text"], "language_hint": c["hint"]}, timeout=90)
    assert r.status_code == 200, r.text[:200]
    d = r.json()
    for k in KEYS:
        assert k in d, f"missing {k}"
    assert d["urgency"] in c["urgency"], f"urgency={d['urgency']}"
    assert d["disclaimer"].strip()
    blob = json.dumps(d, ensure_ascii=False).lower()
    for p in BAD:
        assert not re.search(p, blob), f"forbidden pattern: {p}"
    if c.get("red_flags"):
        assert d["red_flags"], "red_flags empty on urgent case"
    if c.get("no_patterns"):
        assert not d["possible_patterns"] and not d["red_flags"]
    if c.get("min_patterns"):
        assert len(d["possible_patterns"]) >= c["min_patterns"]
    if c.get("mention"):
        assert any(m.lower() in blob for m in c["mention"]), "expected pregnancy mention"
    lang = c.get("lang")
    if lang in SCRIPT:
        assert re.search(SCRIPT[lang], d["summary"]), f"summary not in {lang} script"
    if lang == "en":
        assert not re.search(r"[\u0900-\u097F\u0C80-\u0CFF]", d["summary"]), "summary not English"
    for s in d.get("sources", []):
        sid = s if isinstance(s, str) else s.get("id", "")
        assert re.fullmatch(r"S\d+", sid), f"bad source id {sid}"

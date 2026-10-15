import json, os, pathlib, time, requests
BASE = os.getenv("BASE_URL", "http://localhost:8000")
GAP = int(os.getenv("GAP", "0"))
cases = json.loads((pathlib.Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))
for c in cases:
    d = requests.post(f"{BASE}/analyze", json={"text": c["text"], "language_hint": c["hint"]}, timeout=90).json()
    print(c["id"], "fallback" if d.get("fallback") else "llm", d["urgency"], len(d["possible_patterns"]))
    time.sleep(GAP)
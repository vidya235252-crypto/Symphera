"""Source registry. data/sources.md is the single source of truth.
The model only ever sees IDs + short descriptions; URLs are attached here in code."""
import re
from pathlib import Path

_FILE = Path(__file__).parent / "data" / "sources.md"

# Citable subset. The other entries in sources.md (S5, S6, S8, S9) are blogs/clinic pages that
# the file itself marks as secondary or unverified, so the model is never allowed to cite them.
PREFERRED = ["S1", "S3", "S4", "S7"]
OLDER = ["S2", "S10"]  # published 2014; background only
CITABLE = PREFERRED + OLDER
MAX_CITATIONS = 3

_HEAD = re.compile(r"^\[(S\d+)\]\s+(.+)$")


def _parse() -> dict[str, dict]:
    out: dict[str, dict] = {}
    cur = None
    for line in _FILE.read_text(encoding="utf-8").splitlines():
        m = _HEAD.match(line.strip())
        if m:
            parts = [p.strip() for p in m.group(2).split(" | ")]
            cur = m.group(1)
            out[cur] = {"id": cur, "title": " - ".join(parts[:-1]) or parts[0], "url": parts[-1], "points": []}
        elif cur and line.startswith("- "):
            out[cur]["points"].append(line[2:].strip())
        elif line.startswith("## "):
            cur = None  # stop collecting at the notes section
    return out


REGISTRY = _parse()


def render_for_prompt() -> str:
    """Text block for the system prompt: citable sources only, IDs + titles + key points, no URLs."""
    blocks = []
    for sid in CITABLE:
        s = REGISTRY.get(sid)
        if not s:
            continue
        tag = " (published 2014: cite only if S1, S3, S4, S7 do not cover the point)" if sid in OLDER else ""
        pts = "\n".join(f"- {p}" for p in s["points"])
        blocks.append(f"[{sid}] {s['title']}{tag}\n{pts}")
    return "\n\n".join(blocks)


def map_ids(ids) -> list[dict]:
    """IDs from the model -> [{id,title,url}]. Unknown, non-citable and duplicate IDs are dropped."""
    result, seen = [], set()
    for x in ids if isinstance(ids, list) else []:
        sid = (x.get("id") if isinstance(x, dict) else x)
        sid = sid.strip().upper().strip("[]") if isinstance(sid, str) else None
        if sid in CITABLE and sid in REGISTRY and sid not in seen:
            seen.add(sid)
            s = REGISTRY[sid]
            result.append({"id": s["id"], "title": s["title"], "url": s["url"]})
        if len(result) == MAX_CITATIONS:
            break
    return result


def attach(raw: dict) -> dict:
    return {**raw, "sources": map_ids(raw.get("sources", []))}

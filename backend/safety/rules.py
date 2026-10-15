"""Deterministic pre-LLM safety check. No model involved."""
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_FILE = Path(__file__).parent / "red_flags.json"
_URGENT: list[str] = []
_CRISIS: list[str] = []


def _load():
    if not _URGENT and not _CRISIS:
        data = json.loads(_FILE.read_text(encoding="utf-8"))
        for k, v in data.items():
            if k.startswith("_"):
                continue
            (_CRISIS if k == "crisis" else _URGENT).extend(t.lower() for t in v)
    return _URGENT, _CRISIS


@dataclass
class RuleResult:
    urgent: bool = False
    crisis: bool = False
    matched: list[str] = field(default_factory=list)  # urgent terms only, never crisis terms


def pre_check(text: str) -> RuleResult:
    urgent_terms, crisis_terms = _load()
    norm = re.sub(r"\s+", " ", text.lower())
    hits = [t for t in urgent_terms if t in norm]
    crisis = any(t in norm for t in crisis_terms)
    return RuleResult(urgent=bool(hits) or crisis, crisis=crisis, matched=hits)

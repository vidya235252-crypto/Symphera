import logging
from pydantic import ValidationError

import llm
import fallback
import sources
from schemas import AnalyzeResponse
from safety import rules, guardrails

log = logging.getLogger("pipeline")

_SCRIPT = {"hi": ("\u0900", "\u097f"), "kn": ("\u0c80", "\u0cff")}
_RETRY_NOTE = (
    "Reminder: every string value, including possible_patterns pattern and note, "
    "questions_for_doctor and what_to_track, must be written in the reply language "
    "(not English). Return JSON only."
)


def _wrong_script(resp: AnalyzeResponse) -> bool:
    """True if a hi/kn reply still has long user-facing strings with no characters of that script."""
    rng = _SCRIPT.get(resp.detected_language)
    if not rng:
        return False
    strings = [resp.summary, *resp.questions_for_doctor, *resp.what_to_track]
    for p in resp.possible_patterns:
        strings += [p.pattern, p.note]
    return any(len(s.strip()) >= 8 and not any(rng[0] <= ch <= rng[1] for ch in s) for s in strings)


def run(text: str, language_hint: str = "auto") -> AnalyzeResponse:
    pre = rules.pre_check(text)

    resp = None
    reminder = ""
    for attempt in (1, 2):  # one retry on bad output
        try:
            kw = {"reminder": reminder} if reminder else {}
            cand = AnalyzeResponse.model_validate(sources.attach(llm.analyze(text, language_hint, **kw)))
        except (ValidationError, llm.LLMError) as e:
            log.warning("attempt %d failed: %s", attempt, e)
            continue
        except Exception as e:  # never let an LLM bug become a 500 for the user
            log.exception("unexpected llm failure: %s", e)
            break
        resp = cand
        if attempt == 1 and _wrong_script(cand):
            log.warning("reply language mismatch, retrying with reminder")
            reminder = _RETRY_NOTE
            continue
        break

    if resp is None:
        return fallback.build(language_hint, pre, text)
    return guardrails.apply(resp, pre)

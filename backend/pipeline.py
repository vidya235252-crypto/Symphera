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
    """True if a hi/kn reply has long user-facing strings with no characters of that script."""
    rng = _SCRIPT.get(resp.detected_language)
    if not rng:
        return False

    strings = [resp.summary, *resp.questions_for_doctor, *resp.what_to_track]
    for pattern in resp.possible_patterns:
        strings += [pattern.pattern, pattern.note]

    return any(
        len(value.strip()) >= 8
        and not any(rng[0] <= char <= rng[1] for char in value)
        for value in strings
    )


def run(text: str, language_hint: str = "auto") -> AnalyzeResponse:
    pre = rules.pre_check(text)

    # Handle safety-critical inputs without depending on the model.
    if pre.crisis or pre.urgent:
        return fallback.build(language_hint, pre, text)

    resp = None
    reminder = ""

    for attempt in (1, 2):  # one retry on bad output
        try:
            kwargs = {"reminder": reminder} if reminder else {}
            raw = llm.analyze(text, language_hint, **kwargs)
            candidate = AnalyzeResponse.model_validate(sources.attach(raw))
        except (ValidationError, llm.LLMError) as exc:
            log.warning("attempt %d failed: %s", attempt, exc)
            continue
        except Exception as exc:  # never let an LLM bug become a 500 for the user
            log.exception("unexpected llm failure: %s", exc)
            break

        resp = candidate
        if attempt == 1 and _wrong_script(candidate):
            log.warning("reply language mismatch, retrying with reminder")
            reminder = _RETRY_NOTE
            continue
        break

    if resp is None:
        return fallback.build(language_hint, pre, text)

    return guardrails.apply(resp, pre)
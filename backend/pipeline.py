import logging
from pydantic import ValidationError

import llm
import fallback
from schemas import AnalyzeResponse
from safety import rules, guardrails

log = logging.getLogger("pipeline")


def run(text: str, language_hint: str = "auto") -> AnalyzeResponse:
    pre = rules.pre_check(text)

    resp = None
    for attempt in (1, 2):  # one retry on bad output
        try:
            resp = AnalyzeResponse.model_validate(llm.analyze(text, language_hint))
            break
        except (ValidationError, llm.LLMError) as e:
            log.warning("attempt %d failed: %s", attempt, e)
        except Exception as e:  # never let an LLM bug become a 500 for the user
            log.exception("unexpected llm failure: %s", e)
            break

    if resp is None:
        return fallback.build(language_hint, pre, text)
    return guardrails.apply(resp, pre)

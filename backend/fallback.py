"""Safe response when the LLM fails or returns invalid output. Never shows a stack trace to the user."""
from schemas import AnalyzeResponse
from safety.rules import RuleResult
from safety.guardrails import DISCLAIMERS, URGENT_MSG, CRISIS_MSG

_MSG = {
    "en": "We couldn't analyse this right now. If you are worried about your symptoms, please see a doctor.",
    "hi": "अभी हम इसका विश्लेषण नहीं कर पाए। यदि आप चिंतित हैं तो कृपया डॉक्टर से मिलें।",
    "kn": "ಈಗ ವಿಶ್ಲೇಷಿಸಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ನೀವು ಚಿಂತಿತರಾಗಿದ್ದರೆ ದಯವಿಟ್ಟು ವೈದ್ಯರನ್ನು ಭೇಟಿ ಮಾಡಿ.",
}


def guess_lang(text: str) -> str:
    """Script-based guess, used only when the LLM is unavailable."""
    if any("\u0900" <= ch <= "\u097f" for ch in text):
        return "hi"
    if any("\u0c80" <= ch <= "\u0cff" for ch in text):
        return "kn"
    return "en"


def build(language_hint: str, rules: RuleResult, text: str = "") -> AnalyzeResponse:
    lang = language_hint if language_hint in _MSG else guess_lang(text)
    urgent = rules.urgent
    return AnalyzeResponse(
        detected_language=lang,
        summary=CRISIS_MSG[lang] if rules.crisis else (URGENT_MSG[lang] if urgent else _MSG[lang]),
        red_flags=rules.matched,
        urgency="urgent" if urgent else "soon",
        suggested_specialist="general physician",
        disclaimer=DISCLAIMERS[lang],
    )

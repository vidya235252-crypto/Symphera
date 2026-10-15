"""Deterministic post-LLM guardrails: disclaimer, no diagnosis language, rule override."""
import re
from schemas import AnalyzeResponse
from safety.rules import RuleResult

DISCLAIMERS = {
    "en": "This is general information to help you understand your symptoms, not a diagnosis. Please consult a doctor.",
    "hi": "यह जानकारी केवल समझने के लिए है, निदान नहीं है। कृपया किसी डॉक्टर से सलाह लें।",
    "kn": "ಈ ಮಾಹಿತಿ ಕೇವಲ ತಿಳುವಳಿಕೆಗಾಗಿ, ರೋಗನಿರ್ಣಯವಲ್ಲ. ದಯವಿಟ್ಟು ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
}
URGENT_MSG = {
    "en": "Your description includes warning signs. Please see a doctor or go to the nearest hospital today.",
    "hi": "आपके लक्षणों में चेतावनी के संकेत हैं। कृपया आज ही डॉक्टर से मिलें या नज़दीकी अस्पताल जाएँ।",
    "kn": "ನಿಮ್ಮ ಲಕ್ಷಣಗಳಲ್ಲಿ ಎಚ್ಚರಿಕೆಯ ಸೂಚನೆಗಳಿವೆ. ದಯವಿಟ್ಟು ಇಂದೇ ವೈದ್ಯರನ್ನು ಭೇಟಿ ಮಾಡಿ ಅಥವಾ ಹತ್ತಿರದ ಆಸ್ಪತ್ರೆಗೆ ಹೋಗಿ.",
}

CRISIS_MSG = {
    "en": "You are not alone, and help is available right now. Please call Tele-MANAS on 14416 (free, 24x7, many languages), or 112 in an emergency. If you can, tell someone you trust how you are feeling.",
    "hi": "आप अकेले नहीं हैं, और मदद अभी उपलब्ध है। कृपया Tele-MANAS को 14416 पर कॉल करें (मुफ़्त, 24x7, कई भाषाओं में), या आपात स्थिति में 112 पर कॉल करें। हो सके तो किसी भरोसेमंद व्यक्ति को अपनी हालत बताएँ।",
    "kn": "ನೀವು ಒಬ್ಬರೇ ಅಲ್ಲ, ಈಗಲೇ ಸಹಾಯ ಲಭ್ಯವಿದೆ. ದಯವಿಟ್ಟು Tele-MANAS ಗೆ 14416 ಗೆ ಕರೆ ಮಾಡಿ (ಉಚಿತ, 24x7, ಹಲವು ಭಾಷೆಗಳಲ್ಲಿ), ಅಥವಾ ತುರ್ತು ಪರಿಸ್ಥಿತಿಯಲ್ಲಿ 112 ಗೆ ಕರೆ ಮಾಡಿ. ಸಾಧ್ಯವಾದರೆ ನಂಬಿಕೆಯ ವ್ಯಕ್ತಿಗೆ ನಿಮ್ಮ ಮನಸ್ಥಿತಿ ತಿಳಿಸಿ.",
}

# English diagnosis phrasing -> softened. Non-English relies on C's prompt.
_DIAGNOSIS = re.compile(
    r"\byou (definitely |certainly |probably )?(have|are suffering from|suffer from|got)\b", re.I
)
_SOFT = "your symptoms may be commonly associated with"


def _soften(s: str) -> str:
    return _DIAGNOSIS.sub(lambda m: _SOFT.capitalize() if m.group(0)[0].isupper() else _SOFT, s)


def apply(resp: AnalyzeResponse, rules: RuleResult) -> AnalyzeResponse:
    lang = resp.detected_language if resp.detected_language in DISCLAIMERS else "en"

    resp.summary = _soften(resp.summary)
    for p in resp.possible_patterns:
        p.pattern = _soften(p.pattern)
        p.note = _soften(p.note)

    if rules.urgent:
        resp.urgency = "urgent"
        for term in rules.matched:
            if term not in resp.red_flags:
                resp.red_flags.append(term)
        if rules.crisis:
            if CRISIS_MSG[lang] not in resp.summary:
                resp.summary = f"{CRISIS_MSG[lang]} {resp.summary}"
        elif URGENT_MSG[lang] not in resp.summary:
            resp.summary = f"{URGENT_MSG[lang]} {resp.summary}"

    if not resp.disclaimer.strip():
        resp.disclaimer = DISCLAIMERS[lang]
    return resp

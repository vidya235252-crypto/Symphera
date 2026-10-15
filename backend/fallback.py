"""Safe responses when the LLM fails or safety rules require an immediate response."""

import re

from schemas import AnalyzeResponse, Pattern
from safety.rules import RuleResult
from safety.guardrails import DISCLAIMERS, URGENT_MSG, CRISIS_MSG


_MESSAGES = {
    "en": "I couldn't complete a detailed analysis. If you are concerned, please speak with a clinician.",
    "hi": "मैं पूरा विश्लेषण नहीं कर पाई। अगर आप चिंतित हैं, तो डॉक्टर से बात करें।",
    "kn": "ಪೂರ್ಣ ವಿಶ್ಲೇಷಣೆ ಮಾಡಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. ನಿಮಗೆ ಚಿಂತೆ ಇದ್ದರೆ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
}

_CRISIS_FLAGS = {
    "en": "Thoughts of self-harm",
    "hi": "खुद को नुकसान पहुँचाने के विचार",
    "kn": "ಸ್ವಯಂ ಹಾನಿಯ ಆಲೋಚನೆಗಳು",
}

_GENERAL_SPECIALIST = {
    "en": "general physician",
    "hi": "सामान्य चिकित्सक",
    "kn": "ಸಾಮಾನ್ಯ ವೈದ್ಯರು",
}

_MENTAL_HEALTH_SPECIALIST = {
    "en": "mental health professional",
    "hi": "मानसिक स्वास्थ्य विशेषज्ञ",
    "kn": "ಮಾನಸಿಕ ಆರೋಗ್ಯ ತಜ್ಞರು",
}


def guess_lang(text: str) -> str:
    if any("\u0900" <= char <= "\u097f" for char in text):
        return "hi"
    if any("\u0c80" <= char <= "\u0cff" for char in text):
        return "kn"
    return "en"


def _has_missed_period(text: str) -> bool:
    patterns = (
        r"\bmissed period\b",
        r"\bno period\b",
        r"\bmonths? (?:since|without) (?:my )?period\b",
        r"\bperiod.{0,20}\b(?:didn't|did not|hasn't|has not|not)\b",
        r"पीरियड.{0,20}(?:नहीं|नही)",
        r"महीनों से.{0,20}पीरियड",
        r"ಮುಟ್ಟು.{0,20}(?:ಬಂದಿಲ್ಲ|ಬರಲಿಲ್ಲ)",
    )
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def _symptom_patterns(text: str, lang: str) -> list[Pattern]:
    period = bool(re.search(
        r"\b(period|periods|menstruat|cycle|cycles|पीरियड|माहवारी|ಮುಟ್ಟು)\b"
        r"|(?:period|periods).{0,25}(?:late|irregular|miss|नहीं|ಬಂದಿಲ್ಲ)",
        text,
        re.IGNORECASE,
    ))
    skin_or_hair = bool(re.search(
        r"\b(acne|pimples?|hair|hirsutism|बाल|बालों|चेहरे के बाल|ಮೊಡವೆ|ಕೂದಲು)\b"
        r"|baal|pimples?",
        text,
        re.IGNORECASE,
    ))
    weight = bool(re.search(
        r"\b(weight|वजन|ತೂಕ)\b|bad[heh]|gained",
        text,
        re.IGNORECASE,
    ))

    patterns: list[Pattern] = []

    if period and (skin_or_hair or weight):
        if lang == "hi":
            patterns.append(Pattern(
                pattern="अनियमित पीरियड और अन्य लक्षण",
                note="ऐसे लक्षण PCOS, थायरॉइड की समस्या या दूसरे कारणों से जुड़े हो सकते हैं; डॉक्टर जाँच करके कारण समझ सकते हैं।",
            ))
            patterns.append(Pattern(
                pattern="त्वचा, बाल या वजन में बदलाव",
                note="इन बदलावों के कई कारण हो सकते हैं; इन्हें पीरियड के बदलावों के साथ डॉक्टर को बताएँ।",
            ))
        elif lang == "kn":
            patterns.append(Pattern(
                pattern="ಅನಿಯಮಿತ ಮುಟ್ಟು ಮತ್ತು ಇತರ ಲಕ್ಷಣಗಳು",
                note="ಇವು PCOS, ಥೈರಾಯ್ಡ್ ಸಮಸ್ಯೆ ಅಥವಾ ಇತರ ಕಾರಣಗಳಿಗೆ ಸಂಬಂಧಿಸಿರಬಹುದು; ವೈದ್ಯರು ಪರಿಶೀಲಿಸಿ ಕಾರಣ ತಿಳಿಸಬಹುದು.",
            ))
            patterns.append(Pattern(
                pattern="ಚರ್ಮ, ಕೂದಲು ಅಥವಾ ತೂಕದ ಬದಲಾವಣೆ",
                note="ಈ ಬದಲಾವಣೆಗಳಿಗೆ ಹಲವು ಕಾರಣಗಳಿರಬಹುದು; ಮುಟ್ಟಿನ ಬದಲಾವಣೆಗಳ ಜೊತೆಗೆ ವೈದ್ಯರಿಗೆ ತಿಳಿಸಿ.",
            ))
        else:
            patterns.append(Pattern(
                pattern="Irregular periods with other changes",
                note="These symptoms can be associated with PCOS, thyroid problems, or other causes; a clinician can assess them.",
            ))
            patterns.append(Pattern(
                pattern="Skin, hair, or weight changes",
                note="These changes can have several causes; mention them along with period changes to a clinician.",
            ))

    elif skin_or_hair:
        if lang == "hi":
            patterns.append(Pattern(
                pattern="त्वचा या बालों में बदलाव",
                note="मुंहासे या बालों में बदलाव के कई कारण हो सकते हैं; डॉक्टर से चर्चा करें।",
            ))
        elif lang == "kn":
            patterns.append(Pattern(
                pattern="ಚರ್ಮ ಅಥವಾ ಕೂದಲಿನ ಬದಲಾವಣೆ",
                note="ಮೊಡವೆ ಅಥವಾ ಕೂದಲಿನ ಬದಲಾವಣೆಗಳಿಗೆ ಹಲವು ಕಾರಣಗಳಿರಬಹುದು; ವೈದ್ಯರೊಂದಿಗೆ ಚರ್ಚಿಸಿ.",
            ))
        else:
            patterns.append(Pattern(
                pattern="Skin or hair changes",
                note="Acne or hair changes can have several causes; discuss them with a clinician.",
            ))

    return patterns


def build(
    language_hint: str,
    rules: RuleResult,
    text: str = "",
) -> AnalyzeResponse:
    lang = language_hint if language_hint in _MESSAGES else guess_lang(text)

    if rules.crisis:
        flags = [_CRISIS_FLAGS[lang]]
        summary = CRISIS_MSG[lang]
        urgency = "urgent"
        specialist = _MENTAL_HEALTH_SPECIALIST[lang]
        patterns = []
    elif rules.urgent:
        flags = rules.matched or [URGENT_MSG[lang]]
        summary = URGENT_MSG[lang]
        urgency = "urgent"
        specialist = _GENERAL_SPECIALIST[lang]
        patterns = []
    else:
        flags = []
        patterns = _symptom_patterns(text, lang)
        missed_period = _has_missed_period(text)

        if lang == "hi" and missed_period:
            summary = (
                "पीरियड न आना गर्भावस्था समेत कई कारणों से हो सकता है। "
                "कृपया डॉक्टर से सलाह लें। यह जानकारी निदान नहीं है।"
            )
        elif lang == "kn" and missed_period:
            summary = (
                "ಮುಟ್ಟು ಬಾರದಿರುವುದಕ್ಕೆ ಗರ್ಭಧಾರಣೆ ಸೇರಿದಂತೆ ಹಲವು ಕಾರಣಗಳಿರಬಹುದು. "
                "ದಯವಿಟ್ಟು ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ. ಇದು ರೋಗನಿರ್ಣಯವಲ್ಲ."
            )
        elif lang == "en" and missed_period:
            summary = (
                "A missed period can have several causes, including pregnancy. "
                "Please speak with a clinician. This is not a diagnosis."
            )
        else:
            summary = _MESSAGES[lang]

        urgency = "soon" if patterns or missed_period else "routine"
        specialist = _GENERAL_SPECIALIST[lang]

    return AnalyzeResponse(
        detected_language=lang,
        summary=summary,
        possible_patterns=patterns,
        red_flags=flags,
        urgency=urgency,
        suggested_specialist=specialist,
        disclaimer=DISCLAIMERS[lang],
        fallback=True,
    )
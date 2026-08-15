import re
from typing import Tuple

CRITICAL_KEYWORDS = [
    r"\bsuicid(e|al)\b",
    r"\bkill\s+my\s*self\b",
    r"\bend\s+my\s+life\b",
    r"\bwant\s+to\s+die\b",
    r"\bcan'?t\s+go\s+on\b",
    r"\bself\s*harm\b",
    r"\bcut(ting)?\s+my\s*self\b",
    r"\boverdose\b",
    r"\bno\s+reason\s+to\s+live\b"
]

HIGH_KEYWORDS = [
    r"\bpanic\s+attack\b",
    r"\bcan'?t\s+breathe\b",
    r"\bhopeless(ness)?\b",
    r"\bdesperate\b",
    r"\blosing\s+my\s+mind\b",
    r"\bextreme\b"
]

class RiskEngineService:
    def scan_message_for_distress(self, message: str) -> Tuple[bool, str]:
        text_lower = message.lower()

        for pattern in CRITICAL_KEYWORDS:
            if re.search(pattern, text_lower):
                return True, "CRITICAL"

        for pattern in HIGH_KEYWORDS:
            if re.search(pattern, text_lower):
                return True, "HIGH"

        return False, "NONE"

    def evaluate_composite_risk(
        self,
        phq9_score: int = 0,
        gad7_score: int = 0,
        chat_flag_severity: str = "NONE",
        panic_triggered: bool = False
    ) -> str:
        if panic_triggered or chat_flag_severity == "CRITICAL" or phq9_score >= 20:
            return "CRITICAL"
        
        if chat_flag_severity == "HIGH" or phq9_score >= 15 or gad7_score >= 15:
            return "HIGH"
            
        if phq9_score >= 10 or gad7_score >= 10:
            return "MEDIUM"

        return "LOW"

risk_engine_service = RiskEngineService()

import re
import logging
from typing import Set, Dict, Any, List

logger = logging.getLogger("app.services.response_processor")

def validate_and_strip_citations(text: str, valid_ids: Set[str]) -> str:
    """Finds all [ID] patterns and strips IDs not present in valid_ids."""
    def replacer(match: Any) -> str:
        citation_id = match.group(1)
        if citation_id in valid_ids:
            return match.group(0) # Keep valid
        logger.warning("Stripped hallucinated citation: [%s]", citation_id)
        return "" # Strip invalid

    # Matches [ID] or [ID, ID] etc. Simple regex for [ID]
    return re.sub(r"\[([^\]]+)\]", replacer, text)

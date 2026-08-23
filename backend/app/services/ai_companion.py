# Fix imports and add logger
import os
import httpx
import logging
from typing import List, Dict, Any, Optional, Tuple, Set

logger = logging.getLogger("app.services.ai_companion")

from app.core.config import settings
from app.services.rag_engine import rag_engine
from app.services.response_processor import validate_and_strip_citations

logger = logging.getLogger("app.services.ai_companion")

SYSTEM_PROMPT_TEMPLATE = """You are AURA, an empathetic AI Campus Mental Health Companion for university students.

CRITICAL SAFETY & CLINICAL RULES:
1. You are NOT a doctor, psychiatrist, or licensed therapist.
2. NEVER provide clinical diagnoses, medical advice, or prescribe medications.
3. Explicitly clarify your role as a supportive AI companion if asked.
4. Keep your responses compassionate, active, grounding, and concise (2-4 sentences).
5. If the user expresses intense despair, self-harm, or suicidal thoughts, express care and urge them to use the Panic SOS button or call the helpline (Tele-MANAS: 14416).

PATIENT CLINICAL CONTEXT:
- PHQ-9 Depression Band: {phq9_band}
- GAD-7 Anxiety Band: {gad7_band}

KNOWLEDGE BASE (Grounded Evidence):
{rag_text}

CITATION RULES:
- If your response relies on the provided Knowledge Base, you MUST cite the specific [ID] assigned to relevant chunks. 
- You may ONLY cite IDs present in the context above. Do not invent citation IDs.
- Format: "Your text [doc-id]."
"""

class AICompanionService:
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")

    async def generate_response(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]],
        context_chunks: List[Dict[str, Any]],
        phq9_band: str = "Not Screened",
        gad7_band: str = "Not Screened"
    ) -> Tuple[str, bool]:
        # Assemble grounded context
        valid_ids: Set[str] = set()
        context_str = ""
        for chunk in context_chunks:
            doc_id = chunk["doc_id"]
            valid_ids.add(doc_id)
            context_str += f"<context id='{doc_id}'>\nText: {chunk['text']}\n</context>\n\n"

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            phq9_band=phq9_band,
            gad7_band=gad7_band,
            rag_text=context_str
        )

        reply: str = ""
        used_rag = False

        if self.groq_api_key and len(self.groq_api_key.strip()) > 5:
            try:
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                messages = [{"role": "system", "content": system_prompt}]
                for turn in chat_history[-4:]:
                    messages.append({"role": turn["sender"], "content": turn["content"]})
                messages.append({"role": "user", "content": user_message})

                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages,
                    "temperature": 0.6,
                    "max_tokens": 300
                }

                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        json=payload,
                        headers=headers
                    )
                    if resp.status_code == 200:
                        data = await resp.json()
                        reply = data["choices"][0]["message"]["content"].strip()
                        # Validator: Strip hallucinated citations
                        reply = validate_and_strip_citations(reply, valid_ids)
                        used_rag = True
            except Exception as e:
                logger.error("Groq generation failed: %s", e)
                pass

        if not reply:
            # Fallback (no RAG grounding for fallback)
            reply = "I hear the weight you carry. I'm here to listen. You are not alone."
            
        return reply, used_rag

ai_companion_service = AICompanionService()

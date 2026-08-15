import os
import httpx
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.services.rag_engine import rag_engine

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

RETRIEVED COUNSELOR EXEMPLARS (from clinical dataset for style reference):
{rag_context}
"""

class AICompanionService:
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")

    async def generate_response(
        self,
        user_message: str,
        chat_history: List[Dict[str, str]],
        phq9_band: str = "Not Screened",
        gad7_band: str = "Not Screened"
    ) -> Tuple[str, bool]:
        # Retrieve RAG clinical exemplars
        rag_dialogues = rag_engine.retrieve_relevant_context(user_message, top_k=2)
        rag_str = ""
        for idx, dlg in enumerate(rag_dialogues, 1):
            rag_str += f"Exemplar {idx}:\n- Student: {dlg['input']}\n- Recommended Counselor Style: {dlg['output']}\n\n"

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            phq9_band=phq9_band,
            gad7_band=gad7_band,
            rag_context=rag_str
        )

        # Attempt Groq LLM API if key is present
        if self.groq_api_key and len(self.groq_api_key.strip()) > 5:
            try:
                headers = {
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                }
                
                messages = [{"role": "system", "content": system_prompt}]
                # Append previous 4 turns for conversation context
                for turn in chat_history[-4:]:
                    messages.append({"role": turn["sender"], "content": turn["content"]})
                messages.append({"role": "user", "content": user_message})

                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages,
                    "temperature": 0.6,
                    "max_tokens": 300
                }

                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(
                        "https://api.groq.com/openai/v1/chat/completions",
                        json=payload,
                        headers=headers
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        reply = data["choices"][0]["message"]["content"].strip()
                        return reply, True # True means RAG+Groq used
            except Exception:
                pass

        # Fallback Engine (Offline / Local RAG Synthesis)
        fallback_reply = self._generate_fallback(user_message, rag_dialogues)
        return fallback_reply, False

    def _generate_fallback(self, user_message: str, rag_dialogues: List[Dict[str, str]]) -> str:
        if rag_dialogues and len(rag_dialogues) > 0:
            best_exemplar = rag_dialogues[0]["output"]
            return f"I hear you, and I'm right here with you. {best_exemplar} (Note: I am an AI companion here to support you. If you ever feel in crisis, please click the Panic SOS button above.)"
        
        return "I hear how much weight you are carrying right now. Please take a slow, deep breath with me. I am your AI campus companion—while I cannot provide therapy, I am here to listen. You can also press the Panic SOS button anytime to connect with emergency support."

ai_companion_service = AICompanionService()

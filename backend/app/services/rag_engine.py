import os
import csv
import re
from typing import List, Dict, Any, Tuple

class HybridRAGEngine:
    def __init__(self):
        self.dialogues: List[Dict[str, str]] = []
        self.is_loaded = False

    def load_dataset(self):
        if self.is_loaded:
            return

        # Attempt to locate CSV datasets in root archive directory
        possible_paths = [
            os.path.join(os.getcwd(), "archive", "conversations_training.csv"),
            os.path.join(os.getcwd(), "..", "archive", "conversations_training.csv"),
            os.path.join(os.getcwd(), "archive", "mental_health_conversations.csv"),
            os.path.join(os.getcwd(), "..", "archive", "mental_health_conversations.csv"),
        ]

        csv_path = None
        for p in possible_paths:
            if os.path.exists(p):
                csv_path = p
                break

        if not csv_path:
            # Statically embedded fallback dialogs if dataset file is absent
            self.dialogues = [
                {
                    "input": "I am feeling overwhelmed by exams and constant academic pressure.",
                    "output": "Academic stress can feel all-consuming. Try breaking your tasks into 20-minute chunks and taking deep grounding breaths. What subject is causing the most tension right now?"
                },
                {
                    "input": "I feel lonely and disconnected from everyone around me.",
                    "output": "It takes courage to express feeling isolated. Remember that reaching out—even in small ways—can begin to rebuild connection. Is there someone in your circle you feel comfortable sharing with?"
                },
                {
                    "input": "I can't stop worrying about my future and job prospects.",
                    "output": "Anxiety about what lies ahead is very common among students. Let's focus on what is within your control today. What is one small positive step you can take today?"
                }
            ]
            self.is_loaded = True
            return

        try:
            with open(csv_path, mode="r", encoding="utf-8", errors="ignore") as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    inp = row.get("input") or row.get("question") or row.get("statement")
                    out = row.get("output") or row.get("answer")
                    if inp and out and len(inp.strip()) > 10 and len(out.strip()) > 10:
                        self.dialogues.append({"input": inp.strip(), "output": out.strip()})
                        count += 1
                        if count >= 3000:  # Cap in-memory index size for fast execution
                            break
        except Exception:
            pass

        if not self.dialogues:
            self.dialogues = [
                {
                    "input": "I feel anxious and stressed.",
                    "output": "I hear how heavy that feels. Let's take a slow breath together. Would you like to talk about what triggered this feeling?"
                }
            ]

        self.is_loaded = True

    def _tokenize(self, text: str) -> set:
        words = re.findall(r'\w+', text.lower())
        stopwords = {"i", "me", "my", "myself", "we", "our", "you", "your", "the", "a", "an", "and", "is", "am", "are", "was", "were", "to", "of", "in", "it", "that", "this"}
        return set(w for w in words if w not in stopwords and len(w) > 2)

    def retrieve_relevant_context(self, user_query: str, top_k: int = 2) -> List[Dict[str, str]]:
        if not self.is_loaded:
            self.load_dataset()

        query_tokens = self._tokenize(user_query)
        if not query_tokens:
            return self.dialogues[:top_k]

        scored_dialogues: List[Tuple[float, Dict[str, str]]] = []
        for dlg in self.dialogues:
            inp_tokens = self._tokenize(dlg["input"])
            if not inp_tokens:
                continue
            intersection = query_tokens.intersection(inp_tokens)
            union = query_tokens.union(inp_tokens)
            jaccard_score = len(intersection) / len(union) if union else 0.0
            
            # Boost score if key emotion terms match
            for token in query_tokens:
                if token in dlg["input"].lower():
                    jaccard_score += 0.1

            if jaccard_score > 0:
                scored_dialogues.append((jaccard_score, dlg))

        scored_dialogues.sort(key=lambda x: x[0], reverse=True)
        top_results = [item[1] for item in scored_dialogues[:top_k]]

        if not top_results:
            top_results = self.dialogues[:top_k]

        return top_results

rag_engine = HybridRAGEngine()

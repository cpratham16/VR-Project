import csv
import json
import logging
import os
import hashlib
from typing import Any, Dict, Generator, List, Optional, Set

from app.services.vector_store import vector_store

logger = logging.getLogger("app.services.ingestion")

STATUS_CATEGORY_MAP = {
    "Suicidal": "crisis",
    "Depression": "coping",
    "Anxiety": "coping",
    "Stress": "coping",
    "Bipolar": "psychoeducation",
    "Personality disorder": "psychoeducation",
    "Normal": "general",
}


def _get_hash(val: str) -> str:
    return hashlib.md5(val.strip().lower().encode("utf-8")).hexdigest()


class BaseAdapter:
    """Base category parser and mapping adapter for RAG source ingestion."""

    source_name = "generic"

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path

    def read_records(self) -> Generator[Dict[str, Any], None, None]:
        raise NotImplementedError


class SeedsAdapter(BaseAdapter):
    """Seed curated clinical data json mapping."""

    source_name = "seed_curated"

    def read_records(self) -> Generator[Dict[str, Any], None, None]:
        if not os.path.exists(self.file_path):
            logger.warning("Seed file not found at %s", self.file_path)
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            for item in data:
                yield {
                    "doc_id": item["id"],
                    "text": item["text"],
                    "kind": item["kind"],
                    "category": item["category"],
                    "status": "",
                }


class ConversationsAdapter(BaseAdapter):
    """Archive conversations training csv mapping (input/output QA)."""

    source_name = "conversations_training"

    def read_records(self) -> Generator[Dict[str, Any], None, None]:
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                inp = row.get("input") or ""
                out = row.get("output") or ""
                if len(inp.strip()) > 5 and len(out.strip()) > 5:
                    doc_id = f"ct-{i}"
                    yield {
                        "doc_id": doc_id,
                        "text": f"Question: {inp.strip()}\nAnswer: {out.strip()}",
                        "kind": "qa",
                        "category": "general",
                        "status": "",
                    }


class MentalHealthConversationsAdapter(BaseAdapter):
    """Archive mental health conversations csv mapping (question/answer & statement/status)."""

    source_name = "mental_health_conversations"

    def read_records(self) -> Generator[Dict[str, Any], None, None]:
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                status_raw = (row.get("status") or "").strip()
                cat = STATUS_CATEGORY_MAP.get(status_raw, "general")

                # If question/answer exist, treat as QA. Else treat statement.
                q = row.get("question") or ""
                a = row.get("answer") or ""
                s = row.get("statement") or ""

                if len(q.strip()) > 5 and len(a.strip()) > 5:
                    yield {
                        "doc_id": f"mhc-qa-{i}",
                        "text": f"Question: {q.strip()}\nAnswer: {a.strip()}",
                        "kind": "qa",
                        "category": cat,
                        "status": status_raw,
                    }
                elif len(s.strip()) > 5:
                    yield {
                        "doc_id": f"mhc-st-{i}",
                        "text": s.strip(),
                        "kind": "statement",
                        "category": cat,
                        "status": status_raw,
                    }


class CombinedDataAdapter(BaseAdapter):
    """Combined Data/Combined Data.csv mapping (statement/status)."""

    source_name = "combined_data"

    def read_records(self) -> Generator[Dict[str, Any], None, None]:
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                statement = row.get("statement") or ""
                status_raw = (row.get("status") or "").strip()
                if len(statement.strip()) > 5 and status_raw:
                    cat = STATUS_CATEGORY_MAP.get(status_raw, "general")
                    yield {
                        "doc_id": f"cd-{i}",
                        "text": statement.strip(),
                        "kind": "statement",
                        "category": cat,
                        "status": status_raw,
                    }


class IntentsAdapter(BaseAdapter):
    """Archived combined intents JSON mapping (tag/patterns/responses)."""

    source_name = "combined_intents"

    def read_records(self) -> Generator[Dict[str, Any], None, None]:
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            intents = data.get("intents", [])
            for i, intent in enumerate(intents):
                tag = intent.get("tag") or f"custom-{i}"
                patterns = intent.get("patterns") or []
                responses = intent.get("responses") or []
                if patterns and responses:
                    text_content = (
                        f"Intent Tag: {tag}\n"
                        f"Sample Queries: {'; '.join(patterns[:5])}\n"
                        f"Responses: {'; '.join(responses[:3])}"
                    )
                    yield {
                        "doc_id": f"int-{tag}",
                        "text": text_content,
                        "kind": "intent",
                        "category": "faq",
                        "status": "",
                    }


class RedditAdapter(BaseAdapter):
    """ reddit_mental_health_combined csv mapping (title/text -> peer post)."""

    source_name = "reddit_mental_health"

    def read_records(self) -> Generator[Dict[str, Any], None, None]:
        if not os.path.exists(self.file_path):
            return
        with open(self.file_path, mode="r", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                title = row.get("title") or ""
                body = row.get("text") or ""
                subreddit = row.get("subreddit") or "mentalhealth"
                full_text = f"Title: {title.strip()}\nBody: {body.strip()}" if body.strip() else title.strip()
                if len(full_text.strip()) > 10:
                    yield {
                        "doc_id": f"r-{i}",
                        "text": full_text.strip(),
                        "kind": "post",
                        "category": "peer",
                        "status": "",
                    }


def run_ingest(
    sources_to_run: Optional[List[str]] = None,
    caps: Optional[Dict[str, int]] = None,
    dry_run: bool = False,
    recreate_collection: bool = False,
) -> Dict[str, Any]:
    """Orchestrate source adapters, deduplicate text inputs, cap sizes, and execute upserts.

    Args:
        sources_to_run: List of source names to process. Defaults to all option C.
        caps: Map of source name -> row max limit. Defaults to safe CLI defaults.
        dry_run: Dry run simulation. Returns total counts to be upserted.
        recreate_collection: Wipe existing Qdrant collection before starting.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

    all_adapters = {
        "seeds": SeedsAdapter(os.path.join(base_dir, "backend", "data", "seed_curated.json")),
        "intents": IntentsAdapter(os.path.join(base_dir, "archive", "combined_intents.json")),
        "conversations": ConversationsAdapter(os.path.join(base_dir, "archive", "conversations_training.csv")),
        "mh_conversations": MentalHealthConversationsAdapter(os.path.join(base_dir, "archive", "mental_health_conversations.csv")),
        "combined": CombinedDataAdapter(os.path.join(base_dir, "Combined Data", "Combined Data.csv")),
        "reddit": RedditAdapter(os.path.join(base_dir, "archive", "reddit_mental_health_combined.csv")),
    }

    selected_sources = sources_to_run or list(all_adapters.keys())
    caps = caps or {}

    logger.info("Ingestion job started. Sources: %s, caps: %s", selected_sources, caps)

    # Collect and deduplicate
    seen_hashes: Set[str] = set()
    records_to_insert: List[Dict[str, Any]] = []
    stats: Dict[str, int] = {}

    if recreate_collection and not dry_run:
        logger.info("Wiping existing vector collection.")
        vector_store.delete_document("*")  # simple hook, or recreate. Let's delete collection to be clean:
        if vector_store._collection_exists():
            vector_store._client.delete_collection(vector_store.collection_name)
            vector_store.ensure_collection()

    for name in selected_sources:
        if name not in all_adapters:
            logger.warning("Skipping unknown source: %s", name)
            continue

        adapter = all_adapters[name]
        cap = caps.get(name, 0)
        count = 0
        written = 0

        for rec in adapter.read_records():
            text_hash = _get_hash(rec["text"])
            if text_hash in seen_hashes:
                continue
            seen_hashes.add(text_hash)
            records_to_insert.append(rec)
            count += 1
            written += 1
            if cap and count >= cap:
                logger.info("Cap reached for %s (%d records)", name, cap)
                break

        stats[name] = count

    total_records = len(records_to_insert)
    logger.info("Curation complete: %d unique records gathered.", total_records)

    if dry_run:
        logger.info("[Dry Run] Would have upserted %d records.", total_records)
        return {"status": "dry_run", "gathered_records": total_records, "stats": stats}

    # Batch upsert
    total_chunks = 0
    # Process in batches of 100 docs to keep memory and API call batches balanced
    batch_size = 100
    for i in range(0, len(records_to_insert), batch_size):
        batch = records_to_insert[i : i + batch_size]
        chunks_written = vector_store.upsert_batch(batch)
        total_chunks += chunks_written
        logger.info(
            "Batch %d/%d processed: wrote %d chunks. Total written so far: %d",
            (i // batch_size) + 1,
            (len(records_to_insert) - 1) // batch_size + 1,
            chunks_written,
            total_chunks,
        )

    logger.info("Ingestion completed: %d documents yielded %d chunks", total_records, total_chunks)
    return {"status": "success", "total_documents": total_records, "total_chunks": total_chunks, "stats": stats}

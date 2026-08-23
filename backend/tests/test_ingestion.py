import json
import os
import csv
import tempfile

import pytest
from qdrant_client import QdrantClient

from app.core.config import settings
from app.services.embeddings import reset_provider
from app.services.vector_store import VectorStoreService
from app.services.ingestion import (
    SeedsAdapter,
    ConversationsAdapter,
    MentalHealthConversationsAdapter,
    CombinedDataAdapter,
    IntentsAdapter,
    RedditAdapter,
    STATUS_CATEGORY_MAP,
    run_ingest,
)


@pytest.fixture(autouse=True)
def _reset():
    reset_provider()
    yield
    reset_provider()


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def seed_file(tmp_dir):
    data = [
        {"id": "test-seed-001", "kind": "qa", "category": "coping", "text": "Q: How to calm down?\nA: Try box breathing."},
        {"id": "test-seed-002", "kind": "qa", "category": "crisis", "text": "Q: I feel unsafe.\nA: Call 14416 immediately."},
    ]
    path = tmp_dir / "seed_curated.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


@pytest.fixture
def conversations_file(tmp_dir):
    path = tmp_dir / "conversations_training.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["input", "output"])
        w.writerow(["I feel overwhelmed by exams", "Break tasks into smaller chunks and breathe"])
        w.writerow(["I am lonely", "Reaching out in small ways rebuilds connection"])
        w.writerow(["Hi", ""])  # too short answer, should be skipped
    return str(path)


@pytest.fixture
def combined_data_file(tmp_dir):
    path = tmp_dir / "combined_data.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["", "statement", "status"])
        w.writerow(["0", "I want to end it all", "Suicidal"])
        w.writerow(["1", "trouble sleeping restless heart", "Anxiety"])
        w.writerow(["2", "life is great", "Normal"])
    return str(path)


@pytest.fixture
def intents_file(tmp_dir):
    data = {"intents": [
        {"tag": "greeting", "patterns": ["Hi", "Hello"], "responses": ["Hello! How are you feeling?"]},
        {"tag": "goodbye", "patterns": ["Bye", "See you"], "responses": ["Take care!"]},
    ]}
    path = tmp_dir / "combined_intents.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return str(path)


@pytest.fixture
def reddit_file(tmp_dir):
    path = tmp_dir / "reddit.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "subreddit", "subreddit_type", "title", "text", "author", "score", "created_utc", "num_comments", "sentiment", "category"])
        w.writerow(["1", "ptsd", "ptsd_processed", "family trauma story", "When I was young things were rough", "anon", "10", "0", "2", "", ""])
    return str(path)


def test_seeds_adapter(seed_file):
    adapter = SeedsAdapter(seed_file)
    records = list(adapter.read_records())
    assert len(records) == 2
    assert records[0]["doc_id"] == "test-seed-001"
    assert records[0]["kind"] == "qa"
    assert records[0]["category"] == "coping"
    assert "box breathing" in records[0]["text"]


def test_conversations_adapter_skips_short(conversations_file):
    adapter = ConversationsAdapter(conversations_file)
    records = list(adapter.read_records())
    assert len(records) == 2
    assert all(r["kind"] == "qa" for r in records)


def test_combined_data_adapter_maps_status(combined_data_file):
    adapter = CombinedDataAdapter(combined_data_file)
    records = list(adapter.read_records())
    assert len(records) == 3
    suicidal = [r for r in records if r["status"] == "Suicidal"]
    assert len(suicidal) == 1
    assert suicidal[0]["category"] == "crisis"
    normal = [r for r in records if r["status"] == "Normal"]
    assert normal[0]["category"] == "general"


def test_intents_adapter(intents_file):
    adapter = IntentsAdapter(intents_file)
    records = list(adapter.read_records())
    assert len(records) == 2
    assert records[0]["kind"] == "intent"
    assert records[0]["category"] == "faq"
    assert "greeting" in records[0]["doc_id"]


def test_reddit_adapter(reddit_file):
    adapter = RedditAdapter(reddit_file)
    records = list(adapter.read_records())
    assert len(records) == 1
    assert records[0]["kind"] == "post"
    assert records[0]["category"] == "peer"


def test_status_category_mapping():
    assert STATUS_CATEGORY_MAP["Suicidal"] == "crisis"
    assert STATUS_CATEGORY_MAP["Depression"] == "coping"
    assert STATUS_CATEGORY_MAP["Anxiety"] == "coping"
    assert STATUS_CATEGORY_MAP["Stress"] == "coping"
    assert STATUS_CATEGORY_MAP["Bipolar"] == "psychoeducation"
    assert STATUS_CATEGORY_MAP["Personality disorder"] == "psychoeducation"
    assert STATUS_CATEGORY_MAP["Normal"] == "general"

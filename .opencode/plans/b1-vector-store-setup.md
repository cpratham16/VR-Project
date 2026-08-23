# B1: Vector Store Setup — Execution Plan

## Status
Phase A complete (A1–A6). Starting Phase B. This plan was approved by user with one addition:
inspect both `archive/` and `Combined Data/` folders fully and tune pipeline design to them.

## Data inventory findings (drives schema design)
| File | Rows | Columns | RAG role |
|---|---|---|---|
| archive/conversations_training.csv | 40,237 | input/output | Core counseling exemplar pairs |
| archive/mental_health_conversations.csv | 40,000 | question/answer/source/source_dataset/statement/status | Overlaps conversations_training → dedup in B2 |
| Combined Data/Combined Data.csv | 53,043 | statement/status | Labels: Normal 16351, Depression 15404, Suicidal 10653, Anxiety 3888, Bipolar 2877, Stress 2669, Personality disorder 1201 |
| archive/dialogues_training.csv | 13,118 | text/emotion/act/topic (DailyDialog, __eou__ turns) | Low priority |
| archive/sentiment_analysis.csv | 416,809 | text/source/label(numeric) | D1 classifier reuse, not grounding |
| archive/reddit_mental_health_combined.csv | 588 | id/subreddit/title/text/author/... | Peer-language samples |
| archive/mental_health_comprehensive.csv | 276,143 | TWO fused schemas (CDC survey stats + Suicide_Detection texts w/ class) | Not chatbot-grounding material |
| archive/combined_intents.json | 92 intents | tag/patterns/responses | Canned crisis/smalltalk routing |

Design consequences:
- Payload carries `kind` ∈ {qa, statement, post, intent} + `status`/risk label so B4/B6 can
  filter high-risk-class chunks OUT of generation context; `category` + `source_id` indexed.
- QA records = single chunk each (short); long-form texts use paragraph-aware chunking
  ~1000 chars with ~100 char overlap.
- Bulk ingestion is B2 scope; B1 defines pipeline + proves round-trip.

## Decisions (user-approved)
- Embeddings: **Gemini** `gemini-embedding-001` (free tier) primary via plain httpx
  (matches existing Groq style, no SDK); **fastembed local** fallback when no key → hermetic tests.
- Both providers pinned to **768 dims** (Gemini output_dimensionality=768; fastembed
  nomic-ai/nomic-embed-text-v1.5 = 768) so collections stay interchangeable.
- Qdrant v1.14.0 container + qdrant-client; unit tests use `:memory:` mode.

## Steps
1. docker-compose.yml: add qdrant service (6333/6334, qdrant_data volume, healthcheck).
2. backend/requirements.txt += qdrant-client==1.14.x, fastembed==0.x; pip install into .venv.
3. core/config.py Settings += QDRANT_URL, QDRANT_COLLECTION, EMBEDDING_PROVIDER(auto|gemini|fastembed),
   GEMINI_API_KEY, GEMINI_EMBEDDING_MODEL, FASTEMBED_MODEL, EMBEDDING_DIMENSION=768, CHUNK_SIZE_CHARS=1000,
   CHUNK_OVERLAP_CHARS=100. Mirror into .env.example (+ GEMINI_API_KEY note).
4. NEW services/embeddings.py: embed_documents(list[str]) -> list[list[float]]; provider factory;
   Gemini batchEmbedContents REST call; fastembed ONNX local model.
5. NEW services/vector_store.py: singleton VectorStoreService — ensure_collection (cosine, dim from settings),
   chunk_text(), upsert_document(doc_id, kind, category, status, text) → uuid5 deterministic chunk IDs,
   get_document(doc_id), delete_document(doc_id), count(). Payload: {doc_id, kind, category, status,
   chunk_index, total_chunks, text, created_at}.
6. NEW tests/test_vector_store.py: round-trip test doc — chunked → embedded → upserted → retrieved by ID
   (asserts payload fidelity + chunk count). Uses in-memory Qdrant + forced fastembed provider.
7. Verification: pytest full suite; live round-trip vs Docker Qdrant + Gemini key (user supplies key);
   tsc untouched (backend-only iteration).
8. Close-out per RULES.md §9: inspect diff, update CLAUDE.md, append PROGRESS.md entry, stop.

## Out of scope (later iterations)
B2 bulk ingestion of all corpora; BM25 (B3); touching rag_engine.py/ai_companion.py (B4/B6).

## User setup actions needed at verification step
- Create free API key: https://aistudio.google.com/apikey → put GEMINI_API_KEY=... in backend/.env
- docker compose up -d qdrant

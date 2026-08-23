"""CLI tool to ingest curated content and corpora into Qdrant."""
import argparse
import sys
import logging
from app.services.ingestion import run_ingest

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("seed_rag")

def main():
    parser = argparse.ArgumentParser(description="Ingest RAG datasets into Qdrant.")
    parser.add_argument("--sources", help="Comma-separated list of sources to run")
    parser.add_argument("--cap", type=int, default=1000, help="Max records per source (default 1000)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run — do not upsert")
    parser.add_argument("--recreate", action="store_true", help="Drop collection first")
    
    args = parser.parse_args()
    
    selected = args.sources.split(",") if args.sources else None
    caps = {s: args.cap for s in (selected or ["seeds", "intents", "conversations", "mh_conversations", "combined", "reddit"])}

    try:
        result = run_ingest(
            sources_to_run=selected,
            caps=caps,
            dry_run=args.dry_run,
            recreate_collection=args.recreate
        )
        print(f"Ingestion result: {result['status']}")
        if result.get("total_documents"):
            print(f"Total documents: {result['total_documents']}, Chunks: {result['total_chunks']}")
            
    except Exception as e:
        logger.exception("Ingestion failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
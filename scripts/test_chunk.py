import sys
import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.ingestion import IngestionPipeline, PageModel

pipeline = IngestionPipeline(raw_dir="data/raw_datasheets", processed_dir="data/processed")

def run_chunk_test(text, name):
    print(f"\n--- Testing {name} (Length: {len(text)}) ---")
    page = PageModel(source="test.pdf", page=1, text=text)
    try:
        chunks = pipeline.chunk_page(page, chunk_size=900, overlap=150)
        print(f"Success! Generated {len(chunks)} chunks.")
        for c in chunks:
            print(f"  Chunk {c.chunk_id}: {c.character_count} chars")
    except Exception as e:
        print(f"Failed! Error: {e}")

if __name__ == "__main__":
    # Test 1: Short string (below chunk size)
    short_string = "This is a short string." * 10  # ~230 chars
    run_chunk_test(short_string, "Short String")
    
    # Test 2: Long string (above chunk size)
    long_string = "This is a long string that will definitely span multiple chunks. " * 50  # ~3250 chars
    run_chunk_test(long_string, "Long String")

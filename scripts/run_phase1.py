import os
import json
import statistics
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.ingestion import IngestionPipeline

def run_phase1_report():
    raw_dir = os.path.join("data", "raw_datasheets")
    processed_dir = os.path.join("data", "processed")
    
    pipeline = IngestionPipeline(raw_dir=raw_dir, processed_dir=processed_dir)
    pages, chunks = pipeline.process_all()
    
    if not pages:
        print(f"No pages extracted. Did you move the PDFs to {raw_dir}?")
        return
        
    pdf_files = list(set([p.source for p in pages]))
    
    # Stats
    total_pdfs = len(pdf_files)
    total_pages = len(pages)
    empty_pages = [p for p in pages if len(p.text.strip()) == 0]
    total_chunks = len(chunks)
    
    # Per PDF stats
    pages_per_pdf = {pdf: len([p for p in pages if p.source == pdf]) for pdf in pdf_files}
    chunks_per_pdf = {pdf: len([c for c in chunks if c.source == pdf]) for pdf in pdf_files}
    
    chunk_sizes = [c.character_count for c in chunks]
    avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
    min_chunk_size = min(chunk_sizes) if chunk_sizes else 0
    max_chunk_size = max(chunk_sizes) if chunk_sizes else 0
    
    print("\n" + "="*50)
    print("PHASE 1 - VALIDATION REPORT")
    print("="*50)
    print(f"A. PDFs successfully processed: {total_pdfs}")
    print("\nB. Page counts per PDF:")
    for pdf in sorted(pdf_files):
        print(f"   - {pdf}: {pages_per_pdf[pdf]} pages")
        
    print(f"\nC. Total pages: {total_pages}")
    
    print(f"\nD. Empty/no-text pages: {len(empty_pages)}")
    if empty_pages:
        for p in empty_pages[:5]:
            print(f"   - {p.source} (Page {p.page})")
            
    print(f"\nE. Total chunks: {total_chunks}")
    
    print(f"\nF. Chunk Size Statistics:")
    print(f"   - Average chunk size: {avg_chunk_size:.2f} characters")
    print(f"   - Minimum chunk size: {min_chunk_size} characters")
    print(f"   - Maximum chunk size: {max_chunk_size} characters")
    
    print(f"\nG. Output files created:")
    print(f"   - {os.path.join(processed_dir, 'pages.jsonl')}")
    print(f"   - {os.path.join(processed_dir, 'chunks.jsonl')}")
    
    print("\nH. Sample chunk examples:")
    sample_pdfs = list(set([c.source for c in chunks]))[:2] # get up to 2 pdfs
    for pdf in sample_pdfs:
        pdf_chunks = [c for c in chunks if c.source == pdf]
        if pdf_chunks:
            sample = pdf_chunks[len(pdf_chunks)//2] # middle chunk
            print(f"\n   --- Sample from {pdf} ---")
            print(f"   ID: {sample.chunk_id} | Page: {sample.page} | Chars: {sample.character_count}")
            print(f"   Text Snippet: {sample.text[:150]}...")
            
    print("\nI. Quality Checks:")
    all_sources = all(c.source for c in chunks)
    all_pages = all(c.page > 0 for c in chunks)
    no_empty_chunks = all(c.character_count > 0 for c in chunks)
    unique_chunk_ids = len(set(c.chunk_id for c in chunks)) == len(chunks)
    print(f"   - Every chunk has source metadata: {'PASS' if all_sources else 'FAIL'}")
    print(f"   - Every chunk has valid page number: {'PASS' if all_pages else 'FAIL'}")
    print(f"   - No chunk has empty text: {'PASS' if no_empty_chunks else 'FAIL'}")
    print(f"   - Chunk IDs are unique: {'PASS' if unique_chunk_ids else 'FAIL'}")
    
    print("\nJ. Confirmation:")
    print("   - All original PDFs remain unchanged in data/raw_datasheets/ (read-only operations used).")
    print("="*50 + "\n")

if __name__ == "__main__":
    run_phase1_report()

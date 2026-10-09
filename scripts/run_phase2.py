import os
import json
import time
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.embeddings import EmbeddingService
from src.vectorstore import VectorStore

def run_phase2():
    print("="*50)
    print("PHASE 2 - EMBEDDINGS & CHROMADB")
    print("="*50)
    
    start_total = time.time()
    
    # 1. Load Chunks
    chunks_file = os.path.join(ROOT_DIR, "data", "processed", "chunks.jsonl")
    if not os.path.exists(chunks_file):
        print(f"Error: {chunks_file} not found. Did you run Phase 1?")
        return
        
    chunks = []
    with open(chunks_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks.append(json.loads(line))
                
    source_chunks_count = len(chunks)
    print(f"Loaded {source_chunks_count} chunks from JSONL.")
    
    # Verify IDs are unique and well formed
    unique_ids = set(c["chunk_id"] for c in chunks)
    has_empty = any(not c["text"].strip() for c in chunks)
    
    if len(unique_ids) != source_chunks_count:
        print("Error: Chunk IDs are not unique!")
        return
        
    if has_empty:
        print("Error: Found empty chunks!")
        return
        
    # 2. Init Embedding Service
    print("\nInitializing Embedding Service...")
    embed_service = EmbeddingService()
    emb_dim = embed_service.get_dimension()
    print(f"Embedding dimension: {emb_dim}")
    
    # 3. Generate Embeddings
    print("\nGenerating embeddings (this may take a moment)...")
    texts = [c["text"] for c in chunks]
    
    start_embed = time.time()
    embeddings = embed_service.embed_texts(texts, batch_size=32)
    embed_time = time.time() - start_embed
    print(f"Embedding completed in {embed_time:.2f} seconds.")
    
    # 4. Insert into ChromaDB
    print("\nInitializing ChromaDB...")
    persist_dir = os.path.join(ROOT_DIR, "data", "chroma_db")
    vector_store = VectorStore(persist_dir=persist_dir)
    
    ids = [c["chunk_id"] for c in chunks]
    metadatas = []
    for c in chunks:
        # Keep essential metadata
        meta = {
            "source": c["source"],
            "page": c["page"],
            "chunk_id": c["chunk_id"],
            "character_count": c["character_count"]
        }
        if c.get("section"):
            meta["section"] = c["section"]
        metadatas.append(meta)
        
    print("Inserting records into ChromaDB (upserting to avoid duplicates)...")
    start_insert = time.time()
    vector_store.add_chunks(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    insert_time = time.time() - start_insert
    print(f"Insertion completed in {insert_time:.2f} seconds.")
    
    initial_count = vector_store.get_count()
    
    # 5. Persistence Test
    print("\nRunning persistence test...")
    # Delete the instance to force it to close files/connections (simulating a restart)
    del vector_store
    
    # Reinitialize
    vector_store_reloaded = VectorStore(persist_dir=persist_dir)
    reloaded_count = vector_store_reloaded.get_count()
    persistence_pass = (initial_count == source_chunks_count and reloaded_count == source_chunks_count)
    
    # 6. Semantic Search Smoke Test
    print("\nRunning Semantic Search Smoke Test...")
    test_query = "STM32 microcontroller with Flash memory and GPIO"
    print(f"Query: '{test_query}'")
    
    q_emb = embed_service.embed_texts([test_query])[0]
    results = vector_store_reloaded.search(q_emb, n_results=3)
    
    search_pass = False
    if results and len(results["ids"][0]) > 0:
        search_pass = True
        for i in range(len(results["ids"][0])):
            r_id = results["ids"][0][i]
            r_dist = results["distances"][0][i] if "distances" in results and results["distances"] else "N/A"
            r_meta = results["metadatas"][0][i]
            r_doc = results["documents"][0][i]
            print(f"\n  Result {i+1}:")
            print(f"  Chunk ID: {r_id}")
            print(f"  Source: {r_meta['source']} (Page {r_meta['page']})")
            print(f"  Distance: {r_dist}")
            print(f"  Text preview: {r_doc[:100]}...")
            
    total_time = time.time() - start_total
    
    print("\n" + "="*50)
    print("PHASE 2 REPORT")
    print("="*50)
    print("Data:")
    print(f"- source chunks: {source_chunks_count}")
    print(f"- ChromaDB records: {reloaded_count}")
    print(f"- unique IDs: {len(unique_ids)}")
    print(f"- embedding dimension: {emb_dim}")
    
    print("\nPerformance:")
    print(f"- embedding time: {embed_time:.2f} s")
    print(f"- insertion time: {insert_time:.2f} s")
    print(f"- total time: {total_time:.2f} s")
    
    print("\nValidation:")
    print(f"- metadata: {'PASS' if all(m.get('source') and m.get('page') for m in metadatas) else 'FAIL'}")
    print(f"- duplicates: {'PASS' if reloaded_count == len(unique_ids) else 'FAIL'}")
    print(f"- persistence: {'PASS' if persistence_pass else 'FAIL'}")
    print(f"- semantic search: {'PASS' if search_pass else 'FAIL'}")
    print("="*50)

if __name__ == "__main__":
    run_phase2()

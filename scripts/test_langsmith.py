import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.retrieval import EndToEndRetriever
from src.spec_extractor import SpecExtractor
from src.requirement_parser import RequirementParser
from src.compatibility import CompatibilityEngine
from src.ranking import RankingEngine

def main():
    print("Testing LangSmith Traceability...")
    query = "STM32 MCU with 128KB Flash, 32KB SRAM, 3.3V"
    
    parser = RequirementParser()
    req = parser.parse(query)
    
    retriever = EndToEndRetriever(
        persist_dir=os.path.join(ROOT_DIR, "data", "chroma_db"),
        bm25_dir=os.path.join(ROOT_DIR, "data", "processed")
    )
    chunks = retriever.search(query, dense_k=5, bm25_k=5, final_k=3)
    
    extractor = SpecExtractor()
    spec = extractor.extract(chunks, expected_part_number=req.part_number)
    
    comp_engine = CompatibilityEngine()
    comp_res = comp_engine.evaluate(req, spec)
    
    rank_engine = RankingEngine()
    rank = rank_engine.rank_candidates(req, [(spec, comp_res)])
    
    print("Pipeline executed successfully. Trace should be logged to LangSmith.")
    print("Rank Results:", rank[0].compatibility_status if rank else "None")

if __name__ == "__main__":
    main()

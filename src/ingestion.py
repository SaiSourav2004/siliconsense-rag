import os
import re
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import fitz  # PyMuPDF

class PageModel(BaseModel):
    source: str
    page: int
    text: str
    
class ChunkModel(BaseModel):
    chunk_id: str
    source: str
    page: int
    text: str
    character_count: int
    section: Optional[str] = None

class IngestionPipeline:
    def __init__(self, raw_dir: str, processed_dir: str):
        self.raw_dir = raw_dir
        self.processed_dir = processed_dir
        os.makedirs(self.processed_dir, exist_ok=True)
        
    def validate_and_extract_pages(self, filename: str) -> List[PageModel]:
        filepath = os.path.join(self.raw_dir, filename)
        pages = []
        try:
            doc = fitz.open(filepath)
            for page_num in range(len(doc)):
                # 1-based page number
                actual_page_num = page_num + 1
                page_obj = doc.load_page(page_num)
                raw_text = page_obj.get_text("text")
                cleaned_text = self.clean_text(raw_text)
                
                pages.append(PageModel(
                    source=filename,
                    page=actual_page_num,
                    text=cleaned_text
                ))
            doc.close()
        except Exception as e:
            print(f"Error opening/reading {filename}: {e}")
            
        return pages

    def clean_text(self, text: str) -> str:
        if not text:
            return ""
        # Replace multiple spaces with a single space
        text = re.sub(r'[ \t]+', ' ', text)
        # Replace 3 or more newlines with two newlines (paragraph break)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def chunk_page(self, page_model: PageModel, chunk_size: int = 900, overlap: int = 150) -> List[ChunkModel]:
        chunks = []
        text = page_model.text
        if not text:
            return chunks
            
        # Very simplistic section detection - uppercase lines or specific keywords
        # In a real system, you might use fonts/sizes, but for now we fallback to None
        detected_section = None
        
        # Simple sliding window approach for characters
        start = 0
        text_length = len(text)
        chunk_idx = 1
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            
            # If we are not at the end of the text, try to find a natural break (newline or period)
            if end < text_length:
                # Try to snap to a newline within the last 100 chars of the chunk
                natural_break = text.rfind('\n', max(start, end - 100), end)
                if natural_break != -1:
                    end = natural_break + 1
                else:
                    # Try to snap to a period
                    natural_break = text.rfind('. ', max(start, end - 100), end)
                    if natural_break != -1:
                        end = natural_break + 2
                        
            chunk_text = text[start:end].strip()
            
            if chunk_text:
                # Deterministic chunk ID
                basename = page_model.source.replace('.pdf', '')
                chunk_id = f"{basename}_p{page_model.page}_c{chunk_idx:03d}"
                
                chunks.append(ChunkModel(
                    chunk_id=chunk_id,
                    source=page_model.source,
                    page=page_model.page,
                    text=chunk_text,
                    character_count=len(chunk_text),
                    section=detected_section
                ))
                chunk_idx += 1
                
            if end >= text_length:
                break
                
            start = end - overlap
            
            # Ensure we always move forward if natural break snapping makes start regress or stall
            if start <= end - chunk_size + overlap:
                if end - start < overlap:
                    start = end
                    
        return chunks

    def process_all(self):
        import time
        all_pages = []
        all_chunks = []
        
        if not os.path.exists(self.raw_dir):
            print(f"Directory {self.raw_dir} does not exist.")
            return all_pages, all_chunks
            
        pdf_files = [f for f in os.listdir(self.raw_dir) if f.lower().endswith('.pdf')]
        total_pdfs = len(pdf_files)
        
        start_time_total = time.time()
        
        for i, pdf in enumerate(pdf_files, 1):
            start_time = time.time()
            pages = self.validate_and_extract_pages(pdf)
            all_pages.extend(pages)
            
            pdf_chunks = []
            for page in pages:
                chunks = self.chunk_page(page)
                pdf_chunks.extend(chunks)
                all_chunks.extend(chunks)
                
            elapsed = time.time() - start_time
            print(f"[{i}/{total_pdfs}] Processing: {pdf}")
            print(f"    Pages: {len(pages)}")
            print(f"    Extracted pages: {len(pages)}")
            print(f"    Chunks: {len(pdf_chunks)}")
            print(f"    Time: {elapsed:.2f} seconds")
            
        # Save to jsonl
        pages_file = os.path.join(self.processed_dir, "pages.jsonl")
        chunks_file = os.path.join(self.processed_dir, "chunks.jsonl")
        
        with open(pages_file, "w", encoding="utf-8") as f:
            for p in all_pages:
                f.write(p.model_dump_json() + "\n")
                
        with open(chunks_file, "w", encoding="utf-8") as f:
            for c in all_chunks:
                f.write(c.model_dump_json() + "\n")
                
        total_time = time.time() - start_time_total
        print("\n=== PHASE 1 COMPLETE ===")
        print(f"Total PDFs: {total_pdfs}")
        print(f"Total pages: {len(all_pages)}")
        print(f"Total chunks: {len(all_chunks)}")
        print(f"Total processing time: {total_time:.2f} seconds\n")
        
        return all_pages, all_chunks

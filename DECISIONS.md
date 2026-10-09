# SiliconSense RAG — Engineering Decisions & Development Log

## Purpose

This document records actual implementation decisions, problems, root causes, solutions, validation results, and lessons learned during development. It serves as the permanent engineering decision log for SiliconSense RAG.

---

# Phase 0 — Project Setup

## Objective

Set up the isolated development environment and project structure.

## Implemented

- Virtual environment (venv) created and active.
- `requirements.txt` generated with 12 necessary dependencies (e.g., pymupdf, chromadb, sentence-transformers, rank-bm25, flashrank, pydantic, streamlit, python-dotenv, google-genai, pandas, numpy, langsmith).
- `.env` created for secrets (GEMINI_API_KEY).
- `.gitignore` configured to protect `.env`, `venv/`, `__pycache__/`, `*.pyc`, and `data/chroma_db/`.
- Project folders established (`data/`, `notebooks/`, `src/`, `tests/`, `scripts/`, etc.).
- `notebooks/ChipMatch_RAG_MVP.ipynb` initialized with Phase 1-23 structure.

## Decisions

Environment isolation (venv) and secrets management (.env) were used to ensure reproducibility and prevent accidental commits of sensitive API keys to source control.

## Validation

Verified that folder structure matches requirements, `.gitignore` protects secrets, `.env` holds configuration cleanly, and all 10 raw manufacturer PDFs exist.

## Final Status

PASS

---

# Phase 1 — PDF Ingestion

## Objective

Convert official semiconductor datasheets into reliable, page-aware text chunks while preserving source metadata.

## Dataset

10 official manufacturer datasheets.

## Results

- PDFs: 10
- Pages: 1358
- Chunks: 3301
- Unique chunk IDs: 3301

Generated:
- `data/processed/pages.jsonl`
- `data/processed/chunks.jsonl`

## Implementation

- **PyMuPDF (`fitz`)**: Safely opened and read text from all PDFs.
- **Page-by-page extraction**: Content rigorously isolated by page.
- **Conservative text cleaning**: Whitespace normalization only. No rewriting.
- **Page-aware chunking**: Sliding window chunks created explicitly without crossing boundaries.
- **Approx. 900-character chunks**: With approx. 150-character overlap.
- **No cross-page chunks**: Enforced inherently by the per-page execution loop.
- **Source/page/chunk metadata**: Tied to every single chunk for deterministic evidence tracing.

## Problem 1 — Python import error

**Error:**
`ModuleNotFoundError: No module named 'src'`

**Explain:**
- Where it occurred: When running `scripts/run_phase1.py` and `scripts/test_chunk.py` from the root directory.
- Root cause: Python's `sys.path` did not contain the project root automatically when running a script inside a subdirectory.
- Solution: Project-root path handling was added manually via `sys.path.insert(0, str(ROOT_DIR))` using `pathlib` to reliably import `src.__init__.py` and modules.

## Problem 2 — Chunking infinite loop

**Symptom:**
Phase 1 appeared to hang forever.

**Root cause:**
When the sliding window of the final chunk reached the end of the page text (`end == text_length`), the overlap calculation (`start = end - overlap`) moved the next `start` position backwards repeatedly, causing `start < text_length` to remain forever true.

**Solution:**
Stop when `end >= text_length` using a `break` statement inside the `while` loop, and ensure safe forward progress unconditionally.

## Problem 3 — Chunk test path issue

**Document:**
The isolated test script `scripts/test_chunk.py` was instantiated with `raw_dir=""` and `processed_dir=""`. This caused a `FileNotFoundError: [WinError 3]` when `os.makedirs` was called inside `IngestionPipeline.__init__()` since empty strings are invalid paths on Windows.
The script was corrected to use the safe existing project directories (`data/raw_datasheets` and `data/processed`) to allow memory testing of short and long strings.

## Validation

- 10/10 PDFs processed
- 1358 pages
- 3301 chunks
- 3301 unique chunk IDs
- valid JSONL
- metadata validation passed
- no empty chunks
- original PDFs unchanged

## Independent Validation

The processed JSONL files were independently checked after Phase 1. 

*Important clarification:* While `Get-Content` (PowerShell) reported 3310 physical lines for `chunks.jsonl` (due to potential embedded newlines), strict JSON parsing confirmed exactly 3301 actual JSON records and 3301 unique IDs. We treat 3301 as the authoritative record count because JSON parsing is the correct validation method.

## Key Decisions

1. Preserve strict page boundaries.
2. Do not create chunks across pages.
3. Preserve source/page/chunk metadata.
4. Keep original PDFs untouched.
5. Use UNKNOWN/null rather than guessing missing information later.
6. Preserve the source page so evidence can be cited later.

## Multimodal Decision

The datasheets contain diagrams, pinouts, block diagrams, package diagrams and other visual information. Phase 1 extracts text but does not semantically understand images.

**Decision:**
Do NOT delete or crop diagrams. Keep original PDFs as the authoritative visual source. Visual processing will be integrated later through a controlled multimodal pipeline:

PDF → relevant visual page detection → page rendering → OCR/vision → structured visual evidence → compatibility/evidence layer

Do not send all pages blindly to a vision model.

## Final Status

PASS

---

# Architecture Decisions

## ChromaDB

**Decision:** Use local persistent ChromaDB for MVP.
**Reason:** Simple local vector database and sufficient for the 10-datasheet MVP.

## Embeddings

**Decision:** Use `sentence-transformers/all-MiniLM-L6-v2`.
**Reason:** Local, free, no API key required.

## Keyword Retrieval

**Decision:** Use BM25 (`rank-bm25`).
**Reason:** Important for exact technical terms, part numbers, packages and specification values.

## Hybrid Retrieval

**Decision:** Dense + BM25 → RRF
**RRF formula:** `1 / (60 + rank)`

## Reranking

**Decision:** Use FlashRank after RRF.

## Compatibility

**Decision:** Compatibility must be deterministic Python logic. LLM cannot independently decide compatibility.

## Gemini

**Decision:** Gemini is used for grounded explanation, not authoritative compatibility decisions.

## Evidence

**Decision:** Every important specification/result should remain traceable to: source PDF + page + chunk/evidence ID.

## Observability

**Decision:** Use LangSmith as an optional observability layer.

---

# Development Rules

1. No hallucinated specifications.
2. UNKNOWN is not PASS.
3. No unsupported drop-in replacement claims.
4. Original PDFs remain untouched.
5. No API keys in source code.
6. No fake evaluation metrics.
7. Expensive indexes should not be rebuilt unnecessarily.
8. Each phase must be implemented, tested, validated and reviewed before the next phase.
9. Architecture changes must be recorded in this document.
10. Failed approaches should remain documented rather than silently deleted.

---

# Phase 2 — Embeddings + ChromaDB

## Objective
Convert validated text chunks into local embeddings and store them persistently in ChromaDB.

## Planned Approach
Use SentenceTransformers to generate embeddings and ChromaDB for local persistent storage.

## Implemented
- `src/embeddings.py`
- `src/vectorstore.py`
- `scripts/run_phase2.py`
- `notebooks/ChipMatch_RAG_MVP.ipynb`

## Embedding Model
`sentence-transformers/all-MiniLM-L6-v2`

## Embedding Dimension
384

## ChromaDB Configuration
Persistent local storage at `data/chroma_db/` using collection name `chipmatch_chunks`. Upsert strategy ensures idempotency using stable chunk IDs.

## Problems Encountered
### Problem 1: Windows Hugging Face Cache
### Symptom: Windows Hugging Face cache symlink warning.
### Solution: Non-blocking warning safely ignored.

### Problem 2: Unauthenticated Hugging Face Hub
### Symptom: Warning for unauthenticated hub access.
### Solution: Non-blocking warning safely ignored.

### Problem 3: SentenceTransformer deprecation
### Symptom: `get_sentence_embedding_dimension()` is deprecated.
### Solution: Safely updated to `get_embedding_dimension()`. Non-blocking.

## Validation
- Source chunks: 3301
- ChromaDB records: 3301
- Unique IDs: 3301
- Embedding dimension: 384
- Embedding time: 100.53 seconds
- ChromaDB insertion time: 2.14 seconds
- Total reported time: 335.91 seconds

Validation Checks:
- metadata: PASS
- duplicates: PASS
- persistence: PASS
- semantic search: PASS

*Semantic Smoke Test:*
Query: "STM32 microcontroller with Flash memory and GPIO"
Returned valid STM32 datasheet chunks from:
- DS_stm32f103c8.pdf
- DS_stm32f103rb.pdf
- DS_stm32f401re.pdf

## Decisions Made
- `all-MiniLM-L6-v2`: Local, free, no API keys needed, fast CPU inference.
- `ChromaDB`: Simple local persistent vector store perfect for the MVP.
- `Persistent storage`: Survives process restarts.
- `Stable chunk IDs`: Prevents duplication on reruns.
- `Batch embeddings`: Much faster execution time than iterating one by one.
- `Idempotent ingestion`: Using upsert to allow safe reruns without corrupting data.

## What Changed From Plan
No changes.

## Lessons Learned
Batch execution time on CPU takes ~100s for 3301 chunks, which is extremely efficient for the MVP constraint.

## Final Status
PASS

---

# Retrieval Batch — BM25 + Hybrid RRF + FlashRank

## Objective
Build a high-quality retrieval pipeline that utilizes Dense (ChromaDB), BM25 keyword search, Reciprocal Rank Fusion (RRF), and FlashRank reranking to identify top evidence while preserving all metadata.

## Planned Approach
1. Build a persistent BM25 index on existing chunks.
2. Fuse BM25 and Dense search using RRF formula: `1 / (60 + rank)`.
3. Rerank the top fused candidates using the local FlashRank cross-encoder model.

## Implementation
- `src/bm25_retriever.py`: Built BM25Okapi, serializing the index to disk.
- `src/hybrid_retriever.py`: Executed mathematical fusion.
- `src/reranker.py`: Interfaced with FlashRank model `ms-marco-MiniLM-L-12-v2`.
- `src/retrieval.py`: Built clean End-to-End API.

## Files Changed
- `src/bm25_retriever.py`
- `src/hybrid_retriever.py`
- `src/reranker.py`
- `src/retrieval.py`
- `scripts/run_retrieval_batch.py`

## BM25 Configuration
Index size: 3301 chunks
Top-k: 15

## Dense Retrieval Configuration
Top-k: 15

## RRF Configuration
K parameter: 60

## FlashRank Configuration
Model: `ms-marco-MiniLM-L-12-v2`
Candidates: ≤30 (up to 15 from dense + 15 from BM25)
Final Top-k: 5

## Retrieval Flow
User Query → Dense (15) + BM25 (15) → RRF → FlashRank (Top 5)

## Problems Encountered
### Problem 1: Unauthenticated Hugging Face Hub
### Symptom: Warning: "You are sending unauthenticated requests to the HF Hub."
### Solution: Ignored as a non-blocking warning. Local cache works.

## Validation Results
- Indexed chunks: 3301
- BM25 documents: 3301
- BM25 build time: 0.20 s
- Dense retrieval: ~0.1930 s / query
- BM25 retrieval: ~0.0060 s / query
- RRF time: ~0.0000 s / query
- FlashRank time: ~1.5026 s / query
- Total test time: 266.25 s

Test results:
- BM25: PASS
- Dense: PASS
- RRF: PASS
- FlashRank: PASS
- metadata preservation: PASS
- duplicate handling: PASS
- end-to-end retrieval: PASS

*Qualitative observations:*
- BM25 successfully pinpointed exact part numbers (e.g., `esp32-s3_datasheet_en.pdf`).
- FlashRank confidently pushed semantic matches regarding "STM32 package and GPIO information" to the top (RerankScore ~0.9942).

## Decisions Made
- BM25 index is persisted to disk to avoid 0.20s recalculation on each boot.
- RRF cleanly separated sparse and dense scores without forcing normalization.
- FlashRank limits input to 30 candidates to keep query latency around ~1.5 seconds.
- No source metadata was mutated.

## Changes From Plan
No changes.

## Lessons Learned
FlashRank handles the heavy lifting of the semantic evaluation, so providing it a broad candidate net (Dense + BM25) significantly improves precision without increasing latency drastically.

## Final Status
PASS

---

# Phase 6 & 7 — Requirement Parser and Structured Specification Extraction

## Objective
Convert natural-language requirements into a validated `RequirementSpec` (Phase 6) and map retrieved evidence into a structured `ComponentSpec` (Phase 7) without using LLM hallucinations or changing the existing retrieval pipeline.

## Planned Approach
Use deterministic Python logic (regex/rules) for requirement parsing and structured extraction, leveraging strict Pydantic schemas.

## Implemented
- `src/schemas.py`: `RequirementSpec`, `ComponentSpec`, `Evidence`
- `src/requirement_parser.py`: Deterministic requirement parsing
- `src/spec_extractor.py`: Deterministic evidence extraction

## Files Changed
- `src/schemas.py`
- `src/requirement_parser.py`
- `src/spec_extractor.py`
- `tests/test_requirement_parser.py`
- `tests/test_spec_extractor.py`
- `scripts/run_phase6_7.py`
- `notebooks/ChipMatch_RAG_MVP.ipynb`

## Problems Encountered
### Problem: Component Identity Leakage
### Symptom: `STM32F103C8` query mistakenly retrieved and used `STM32F411RE` evidence.
### Root Cause: The initial extractor had no awareness of candidate identity, accepting any Flash/SRAM specs found in semantically similar chunks.
### Fix: Added `part_number` to `RequirementSpec`. Updated parser to extract the target part. Updated `SpecExtractor.extract()` to accept `expected_part_number` and filter out chunks from unrelated PDFs before extraction.

## Validation Results
- Pytest runtime: 0.17s
- Tests collected: 11
- Tests passed: 11
- Tests failed: 0

### Real Smoke Test (Before Behavior):
Query: `STM32F103C8 Flash SRAM GPIO voltage`
Result: Extracted 512KB Flash and 128KB SRAM erroneously from `DS_stm32f411re.pdf`.

### Real Smoke Test (After Behavior):
Query: `STM32F103C8 Flash SRAM GPIO voltage`
Result: Wrong-component evidence correctly rejected. Extracted Flash: UNKNOWN, SRAM: UNKNOWN, Voltage: UNKNOWN.

Validation checks:
- Provenance validation: PASS
- Missing-value handling: PASS
- Conflict handling: PASS
- Fabrication/hallucination protection: PASS
- Retrieval architecture changed: NO

## Decisions Made
- Deterministic extraction: Enforces 100% adherence to actual retrieved evidence. Missing data defaults to UNKNOWN.
- Identity Guard: Component filtering added precisely at the extraction boundary instead of modifying the complex Dense+BM25+RRF pipeline.

## What Changed From Plan
No changes.

## Lessons Learned
Retrieval systems prioritize semantic relevance over strict categorical boundaries. A query for one component will naturally fetch text from another similar component. Explicit identity safeguards must exist at the extraction boundary to prevent "specification stealing."

## Final Status
Phase 6: PASS
Phase 7: PASS

---

# Phase 8 — Deterministic Compatibility Engine

## Objective
Transform the parsed `RequirementSpec` and the extracted `ComponentSpec` (along with its `Evidence`) into deterministic constraint-level evaluations and an overall candidate compatibility decision using pure Python logic, without LLM hallucinations.

## Planned Approach
Define strict rules for each specification type (voltage, memory, interfaces, package). Introduce `ConstraintResult` and `CompatibilityResult` schemas to structure the engine's output in a machine-readable, traceable format. 

## Implemented
- **Schemas**: `ConstraintResult` and `CompatibilityResult` in `src/schemas.py`.
- **Engine**: `CompatibilityEngine` in `src/compatibility.py`.
- **Rules**:
  - *Voltage*: Valid interval overlap (`comp.min <= req.max` AND `comp.max >= req.min`).
  - *Flash/SRAM/GPIO*: Simple threshold checks (`comp >= req`).
  - *Frequency*: Value must fall within the required min/max interval.
  - *Interfaces*: Required interfaces must be a subset of supported interfaces.
  - *Package*: Basic text normalization and exact matching.
  - *Decision Priority*: `FAIL` > `UNKNOWN` > `PASS`. An overall candidate is rated `INCOMPATIBLE` if any required constraint fails, `INSUFFICIENT_EVIDENCE` if any remains unknown, and `POTENTIAL_MATCH` if all pass.

## Files Changed
- `src/schemas.py`
- `src/compatibility.py`
- `tests/test_compatibility_engine.py`
- `scripts/run_phase8.py`
- `scripts/test_chunk.py` (Regression fix)

## Problems Encountered
### Problem: Pytest Collection Error
### Symptom: `scripts/test_chunk.py::test_chunk` caused Pytest to crash looking for `text` fixture.
### Root Cause: Pytest automatically collects functions starting with `test_` as tests. The manual validation script contained a helper function named `test_chunk(text, name)` which broke the suite.
### Fix: Cleanly renamed the helper to `run_chunk_test` and updated callers within the script. The manual functionality was perfectly preserved while resolving the test runner conflict.

## Validation Results
- **Unit Tests**: `test_compatibility_engine.py` ran 30/30 tests successfully in 0.17s.
- **Regression**: The full suite ran 41 tests successfully in 0.33s with 0 errors.

### Real Smoke Test Outcomes:
- **Candidate A**: `POTENTIAL_MATCH` (All constraints, including voltage 3.0-3.6 and memory requirements, explicitly passed).
- **Candidate B**: `INCOMPATIBLE` (Flash requirement of 256KB failed against actual 128KB).
- **Candidate C**: `INSUFFICIENT_EVIDENCE` (SRAM constraint evaluated to UNKNOWN due to missing evidence).

## Decisions Made
- Prioritized hard failing. A missing piece of evidence (UNKNOWN) will never secretly pass or fail a component, but it will drop the overall component to `INSUFFICIENT_EVIDENCE`.
- Kept logic entirely within Python `if/else` bounds to guarantee stability.

## What Changed From Plan
No changes. Architecture and logic executed exactly as planned.

## Lessons Learned
Naming conventions in Python (like `test_`) have powerful side effects due to standard testing frameworks. Even in non-test script directories, utility functions must avoid reserved prefixes to prevent pipeline breakages.

## Final Status
Phase 8: PASS

---

# Phase 9 — Deterministic Candidate Ranking

## Objective
Implement a deterministic ranking engine to sort component candidates based on compatibility tier, evidence completeness, and numerical margins, ensuring hard constraints are never overridden by soft preference scores.

## Planned Approach
Create a two-pass sorting algorithm (`RankingEngine`) that first groups candidates by a strict compatibility tier (`POTENTIAL_MATCH` > `INSUFFICIENT_EVIDENCE` > `INCOMPATIBLE`) and then ranks them internally using a normalized 0-100 soft score based on evidence completeness and positive margins.

## Implemented
- **Schemas**: `CandidateRanking` in `src/schemas.py`.
- **Engine**: `RankingEngine` in `src/ranking.py`.
- **Rules**:
  - *Hard Gate*: `POTENTIAL_MATCH` (3) > `INSUFFICIENT_EVIDENCE` (2) > `INCOMPATIBLE` (1).
  - *Score*: Max 50 points for completeness (known vs total constraints). Max 50 points for numeric margins (up to 15 points per matched numeric constraint).
  - *INCOMPATIBLE Handling*: `score` is set to `None`, and no margin/completeness scoring is executed to prevent misleading positive signals for failing candidates.
  - *UNKNOWN Handling*: Drops completeness score, adds `"Score is provisional due to missing constraints."` reason.
  - *Tie-Breaking*: Stable sort via `Part Number`. `None` scores map to `-1.0` during tie-breaking.

## Files Changed
- `src/schemas.py`
- `src/ranking.py`
- `tests/test_ranking.py`
- `scripts/run_phase9.py`

## Problems Encountered
### Problem: Misleading Incompatible Score
### Symptom: `INCOMPATIBLE` Candidate D was initially assigned a soft score of `65.0`. Though it was correctly placed at the bottom by the Hard Gate tier sort, displaying a positive preference score for a failing candidate was highly misleading.
### Root Cause: The scoring loop indiscriminately evaluated numeric margins even if the candidate had already failed a hard constraint.
### Fix: Updated the schema to allow `score: Optional[float] = None`. Modified the engine to assign `score = None` for `INCOMPATIBLE` candidates and bypassed soft scoring logic. Handled the `None` case gracefully in tie-breaking logic (`x.score if x.score is not None else -1.0`).

## Validation Results
- **Unit Tests**: `test_ranking.py` ran 10/10 tests successfully.
- **Regression**: The full suite ran 51 tests successfully with 0 errors.

### Real Smoke Test Outcomes:
- **Candidate A**: `POTENTIAL_MATCH`, Score `80.0`
- **Candidate B**: `POTENTIAL_MATCH`, Score `50.0`
- **Candidate C**: `INSUFFICIENT_EVIDENCE`, Score `40.0` (Provisional)
- **Candidate D**: `INCOMPATIBLE`, Score `None`

## Decisions Made
- `score` made `Optional[float]` to strictly differentiate between a preferred component and a fundamentally broken one.
- Preserved missing evidence uncertainty by explicitly tagging provisional scores.

## What Changed From Plan
Adjusted the schema and scoring application logic during the audit to omit soft scoring entirely for `INCOMPATIBLE` candidates.

## Lessons Learned
Sorting by tiers isn't enough; the data representation itself must reflect the invalidity of failed candidates. A soft score implies a valid tradeoff, which is dangerous when hard compatibility fails.

## Final Status
Phase 9: PASS

---

# Phase 10 — Evidence & Citation Layer

## Objective
Make every decision auditable by rendering the `Evidence` object attached to each specification, presenting exactly which datasheet, page, chunk, and excerpt led to the compatibility outcome. Ensure strict Component Identity is maintained and conflicts/missing values are surfaced explicitly without LLM hallucination.

## Planned Approach
Create an `EvidenceFormatter` in `src/evidence.py` to convert the `CompatibilityResult` into a structured, user-facing trace. Re-verify the voltage extraction logic and integration status.

## Implemented
- **Files Created**: `src/evidence.py` containing `EvidenceFormatter`, `tests/test_evidence.py`, `scripts/run_phase10.py`.
- **Validation**:
  - `EvidenceFormatter` securely truncates text, correctly reports `UNKNOWN`, and strictly prints the `source`, `page`, and `chunk_id`.

## Problems Encountered
### Problem: Voltage Discrepancy in Mock
### Symptom: The Phase 10 smoke test reported a voltage failure (`1.8` vs `3.0`) but the overall component was incorrectly mocked as `INSUFFICIENT_EVIDENCE`.
### Root Cause: The mocked object in `scripts/run_phase10.py` incorrectly hardcoded the overall status instead of utilizing the `src/compatibility.py` engine, which strictly prioritizes `FAIL` over `UNKNOWN`.
### Fix: Corrected the mock object's overall status to `INCOMPATIBLE`. Verified that the existing `SpecExtractor` uses `re.finditer(r'(\d+\.?\d*)\s*v\s*(?:to|-)\s*(\d+\.?\d*)\s*v', text)` to correctly parse operating intervals, meaning `1.8 to 2.5 V` accurately fails a `3.0 V` constraint.

## Validation Results
- **Unit Tests**: `test_evidence.py` ran successfully.
- **Regression**: The full suite passed successfully (55 tests).
- **Real Smoke Test**: Output accurately rendered the evidence strings and `INCOMPATIBLE` outcome.

## Final Status
Phase 10: PASS

---

# Phase Update Template

## Phase X — <Name>

### Objective

### Planned Approach

### Implemented

### Files Changed

### Problems Encountered

### Root Causes

### Solutions

### Validation

### Results

### Decisions Made

### What Changed From Plan

### Lessons Learned

### Final Status

---

# Phase 11 — Evaluation

## Objective
Establish honest retrieval and extraction metrics using a preliminary set of queries, evaluating Hit Rate@K, MRR@K, Recall@K, and exact match extraction accuracy.

## Planned Approach
Run an evaluation loop over a predefined dataset of queries to quantify system performance. 

## Implemented
- **Files Changed**: `scripts/evaluate_phase11.py`, `src/evaluation.py`, `tests/test_evaluation.py`
- Evaluated against a preliminary 3-query dataset.

## Validation Results
- **Queries Evaluated**: 3
- **Top-1 Metrics**:
  - Hit Rate@1: 0.3333
  - MRR@1: 0.3333
  - Recall@1: 0.3333
- **Top-5 Metrics**:
  - Hit Rate@5: 0.6667
  - MRR@5: 0.4000
  - Recall@5: 0.6667
- **Extraction Evaluation (Exact Match)**:
  - Flash: 1/3
  - SRAM: 0/3
  - Voltage: 1/3

## Decisions Made
- Use a small (3-query) dataset for initial pipeline validation before investing in large-scale manual annotation.
- Acknowledge that the current metrics are preliminary and do not represent a production-quality or comprehensive evaluation.

## Final Status
Phase 11: PASS (Local / Preliminary Validation)

---

# Phase 12 — Gemini Grounded Explanation

## Objective
Provide an engineering summary of the compatibility status using an LLM, without allowing it to recalculate scores, alter constraints, or hallucinate compatibility.

## Planned Approach
Pass the deterministic constraint results and evidence trace to Gemini to generate a structured `ExplanationResponse`. Ensure strict validation of the LLM's output.

## Implemented
- **Files Changed**: `src/explainer.py`, `scripts/run_phase12.py`, `tests/test_explainer.py`
- Implemented `GeminiExplainer` to format the prompt and parse the structured output.
- Added validation logic to reject contradictory claims (e.g., LLM claiming a part is "compatible" despite an `INCOMPATIBLE` overall status).
- Added an offline fallback mechanism when the API key is missing or validation fails.

## Validation Results
- **Unit Tests**: `test_explainer.py` passed, including the regression test for contradictory claims (`test_explainer_rejects_contradictory_incompatible_claim`).
- **Smoke Test**: `scripts/run_phase12.py` successfully executed in Mock Mode (offline fallback) outputting: `Summary: The candidate STM32F103C8 is INCOMPATIBLE. It failed on: voltage, flash_kb. It lacked evidence for: sram_kb.`

## Decisions Made
- **Validation**: Enforce a strict integrity check on the LLM's summary output. If the candidate is `INCOMPATIBLE`, reject claims like "is compatible" or "perfect match" and use the structured fallback.
- **Mock/Offline Mode**: Document Phase 12 as mock/offline-fallback validated. We do not claim successful real Gemini API validation since it was executed in a mock environment without an active API key during these tests.

## Final Status
Phase 12: PASS (Mock/Offline Fallback Validated)

---

# Phase 13 — Streamlit UI

## Objective
Build a professional Streamlit application to surface the underlying RAG pipeline, providing search, structured constraints, candidate ranking, constraint validation visualization, evidence citations, and Gemini explanations.

## Planned Approach
Map user inputs to `RequirementParser`, execute `EndToEndRetriever`, group evidence by candidate `part_number`, perform `SpecExtractor` on each, run the `CompatibilityEngine` and `RankingEngine`, and display results.

## Implemented
- **Files Changed**: `app.py` (created), `tests/test_ui.py` (created)
- Built interactive sidebars for requirements.
- Integrated the full pipeline flow: Parsing -> Retrieval -> Extraction -> Compatibility -> Ranking -> Explanation.
- Formatted tables for constraint breakdown and markdown expanders for candidate rankings.
- Passed along all `Evidence` objects visually to the user, ensuring source citations are clearly visible.

## Validation Results
- **Unit Tests**: Added `test_missing_evidence_ui_handling` and `test_gemini_explainer_fallback` in `tests/test_ui.py`.
- **Suite**: 67/67 tests passed.
- **Constraints Visualized**: Yes, constraints properly surface actual values vs requirements and their status.
- **Missing Evidence handling**: Surfaced effectively using UNKNOWN states without treating it as PASS.

## Decisions Made
- Candidates are dynamically constructed by scanning the retrieved chunk sources (e.g. `DS_stm32f103c8.pdf` -> `STM32F103C8`) and re-running `SpecExtractor` for each identified component part number.
- Gemini is strictly called *after* deterministic ranking, and its limitations/fallback states are fully exposed in the UI.
- No business logic or scoring algorithms were duplicated into Streamlit.

## Final Status
Phase 13: PASS

## Phase 14 & 15: LangSmith Observability & Evaluation Dataset
- **LangSmith Integrated**: Added @traceable decorators to RequirementParser, EndToEndRetriever, HybridRetriever, FlashRankReranker, SpecExtractor, CompatibilityEngine, RankingEngine, and GeminiExplainer. Native fail-open behavior is handled by the SDK.
- **Evaluation Dataset**: Expanded eval_queries.json to 15 diverse queries (exact matches, alternative parts, missing specs, incompatible candidates).
- **Extraction Logic Fix**: Removed strict part_mentions disambiguation in SpecExtractor which failed to extract anything when exact parts were masked as family codes (e.g. STM32F103x8 vs STM32F103C8).
- **Limitation Documented**: Structured extraction relying purely on regex performs poorly on datasheet tables. Retrieval hits 93.3% Top-5 Hit Rate, but table extraction requires multimodal/OCR solutions in future phases. No fabricated metrics are presented.

## Phase 16: Failure Analysis and Reliability
- **UI Reliability**: Added 	ry-except blocks around the retrieval pipeline in pp.py to prevent Streamlit from crashing on missing databases or network failures.
- **LLM Fallback**: GeminiExplainer natively catches Exception during generation (timeouts, quotas, connection errors) and gracefully falls back to deterministic rule summaries, guaranteeing the app does not break.

## Phase 17: Final UI and End-to-End Verification
- **UI Testing**: Implemented a comprehensive smoke test using Streamlit AppTest framework (scripts/test_ui_smoke.py). The test successfully loads the app, injects a query, simulates a button click, executes the entire pipeline (Retrieval -> Extraction -> Compatibility -> Ranking), and verifies the output headers without requiring a browser subagent.

## Phase 19 & 20: Deployment Preparation & Production Monitoring
- **Deployment Configured**: Adjusted .gitignore to track data/chroma_db/ and data/processed/ since this is a portfolio project and re-ingesting on every Streamlit Cloud cold start is inefficient. Created docs/DEPLOYMENT.md with explicit platform instructions.
- **Monitoring Configured**: Relying on LangSmith SDK for tracing (latency, I/O, error captures). Documented operational readiness and failure runbooks in docs/MONITORING.md.

## Phase 21: CI, Regression Protection and Release
- **Continuous Integration**: Added GitHub Actions workflow (.github/workflows/ci.yml) to automatically run the deterministic pytest unit test suite and the Streamlit AppTest smoke test on every push to main and PRs. This prevents regression without burning API quotas.

## Phase 22: Final Portfolio Quality
- **Documentation Overhaul**: Authored a clear, engineering-focused README.md that explicitly states the architectural constraints (deterministic extraction/evaluation, grounded LLM explanation). The PLAN.md has been marked 100% complete for all textual RAG components.

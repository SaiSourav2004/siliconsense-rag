import streamlit as st
import os
import re

from src.requirement_parser import RequirementParser
from src.retrieval import EndToEndRetriever
from src.spec_extractor import SpecExtractor
from src.compatibility import CompatibilityEngine
from src.ranking import RankingEngine
from src.explainer import GeminiExplainer
from src.schemas import RequirementSpec

st.set_page_config(page_title="SiliconSense RAG", layout="wide")

@st.cache_resource
def get_retriever():
    return EndToEndRetriever(persist_dir="data/chroma_db", bm25_dir="data/processed")

retriever = get_retriever()
parser = RequirementParser()
extractor = SpecExtractor()
compatibility_engine = CompatibilityEngine()
ranking_engine = RankingEngine()
explainer = GeminiExplainer()

st.title("SiliconSense RAG: Evidence-Grounded Screening")
st.markdown("⚠️ **Disclaimer**: Results are preliminary engineering screening. Datasheets must be manually verified.")

# --- Sidebar Inputs ---
st.sidebar.header("Search & Requirements")

query = st.sidebar.text_area("Natural Language Query", "STM32 MCU with 128KB Flash, 32KB SRAM, 3.3V")
parsed_req = parser.parse(query)

st.sidebar.subheader("Parsed / Overrides")
part_num = st.sidebar.text_input("Target Part Number (Optional)", value=parsed_req.part_number or "")
flash = st.sidebar.number_input("Min Flash (KB)", value=parsed_req.min_flash_kb or 0)
sram = st.sidebar.number_input("Min SRAM (KB)", value=parsed_req.min_sram_kb or 0)
gpio = st.sidebar.number_input("Min GPIO", value=parsed_req.min_gpio or 0)
vmin = st.sidebar.number_input("Voltage Min (V)", value=parsed_req.voltage_min or 0.0)
vmax = st.sidebar.number_input("Voltage Max (V)", value=parsed_req.voltage_max or 0.0)

if st.sidebar.button("Search Candidates"):
    with st.spinner("Retrieving evidence and evaluating candidates..."):
        # Update requirement spec
        req = RequirementSpec()
        req.part_number = part_num if part_num else None
        req.min_flash_kb = flash if flash > 0 else None
        req.min_sram_kb = sram if sram > 0 else None
        req.min_gpio = gpio if gpio > 0 else None
        req.voltage_min = vmin if vmin > 0 else None
        req.voltage_max = vmax if vmax > 0 else None
        req.interfaces = parsed_req.interfaces
        req.package = parsed_req.package
        req.frequency_min_mhz = parsed_req.frequency_min_mhz
        req.frequency_max_mhz = parsed_req.frequency_max_mhz
        req.connectivity = parsed_req.connectivity

        if not query.strip() and not part_num:
            st.error("Please provide a natural language query or a target part number.")
            st.stop()

        try:
            # 1. Retrieve chunks
            # Increase K to get enough chunks for multiple potential candidates
            chunks = retriever.search(query, dense_k=30, bm25_k=30, final_k=15)
        except Exception as e:
            st.error(f"System Error during retrieval: {str(e)}")
            chunks = []
        if not chunks:
            st.warning("No evidence chunks retrieved. Try refining your query.")
        else:
            # 2. Identify candidate parts from chunk sources
            candidates_sources = set([c['source'] for c in chunks])
            
            # Map source file name to a part number string (e.g. DS_stm32f103c8.pdf -> STM32F103C8)
            candidate_parts = []
            for src in candidates_sources:
                m = re.search(r'(stm32[a-z0-9]+|esp32[a-z0-9\-]*)', src.lower())
                if m:
                    candidate_parts.append(m.group(1).upper())
                else:
                    candidate_parts.append(src)
            candidate_parts = list(set(candidate_parts))

            candidates_data = []
            
            for part in candidate_parts:
                # 3. Extract spec for this specific part
                comp_spec = extractor.extract(chunks, expected_part_number=part)
                comp_spec.part_number = part
                
                # 4. Evaluate compatibility
                comp_res = compatibility_engine.evaluate(req, comp_spec)
                candidates_data.append((comp_spec, comp_res))

            # 5. Rank candidates
            ranked_candidates = ranking_engine.rank_candidates(req, candidates_data)

            # Display Results
            st.header("Candidate Rankings")
            
            for rank in ranked_candidates:
                # Find corresponding comp_res
                comp_res = next(res for spec, res in candidates_data if res.part_number == rank.part_number)
                
                is_target = req.part_number and rank.part_number.upper() == req.part_number.upper()
                label = "🎯 [Target Part]" if is_target else "🔄 [Alternative Candidate]" if req.part_number else ""

                
                with st.expander(f"Rank {rank.rank}: {rank.part_number} {label} - {rank.compatibility_status}"):
                    # Status and Score
                    col1, col2 = st.columns(2)
                    col1.metric("Status", rank.compatibility_status)
                    score_val = f"{rank.score:.1f}" if rank.score is not None else "N/A"
                    col2.metric("Score", score_val)
                    
                    st.write("**Ranking Reasons:** " + "; ".join(rank.ranking_reasons))
                    
                    # Constraints Table
                    st.subheader("Constraints")
                    st.markdown("""
| Constraint | Required | Actual | Status | Reason |
|---|---|---|---|---|
""" + "\n".join([f"| {c.constraint} | {c.required_value} | {c.actual_value} | {c.status} | {c.reason} |" for c in comp_res.constraint_results]))
                    
                    # Evidence Trace
                    st.subheader("Evidence Citations")
                    if comp_res.evidence:
                        for ev in comp_res.evidence:
                            st.info(f"**{ev.field}** = {ev.value} (Source: {ev.source}, Page: {ev.page})\n\n*\"{ev.evidence_text}\"*")
                    else:
                        st.write("No positive evidence found.")

                    # Gemini Explanation
                    st.subheader("AI Explanation")
                    with st.spinner("Generating explanation..."):
                        try:
                            explanation = explainer.explain(req, comp_res, rank)
                            st.write(f"**Summary:** {explanation.summary}")
                            
                            if explanation.evidence_backed_claims:
                                st.write("**Verified Claims:**")
                                for claim in explanation.evidence_backed_claims:
                                    st.write(f"- {claim}")
                                    
                            if explanation.uncertainties:
                                st.write("**Missing Info:**")
                                for u in explanation.uncertainties:
                                    st.write(f"- {u}")
                            
                            st.caption(explanation.limitations)
                        except Exception as e:
                            st.warning(f"Explanation could not be generated: {str(e)}")

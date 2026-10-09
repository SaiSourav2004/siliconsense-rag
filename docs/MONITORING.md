# Production Monitoring & Operational Readiness

## 1. Primary Monitoring: LangSmith
This application uses **LangSmith** as its primary observability and monitoring platform. 

### What is tracked:
- **End-to-End Latency**: Tracked at the `chain` level (from query input to final explanation).
- **Sub-Component Latency**:
  - Dense Retrieval execution time
  - FlashRank Reranking execution time
  - Gemini API generation time
- **Error Rates**: Any exceptions thrown in the retrieval pipeline or LLM generation are captured with full stack traces in LangSmith.
- **Pipeline Inputs/Outputs**: 
  - The parsed `RequirementSpec`
  - The retrieved context chunks
  - The deterministic `CompatibilityResult`
  - The final `ExplanationResponse`

### Accessing Logs
Navigate to your LangSmith project (`siliconsense-rag`). 

## 2. Infrastructure Health (Streamlit Cloud)
If deployed on Streamlit Community Cloud:
- Streamlit automatically restarts the instance on critical OOM (Out of Memory) errors.
- The `app.py` script catches internal routing and retrieval errors safely via `try/except` without taking down the UI session state.

## 3. Alerts & Thresholds
For a portfolio project, active alerting (PagerDuty/Slack) is not configured by default. 
If needed for production, you can configure **LangSmith Automations** to trigger webhooks when:
- Error rate exceeds 5% in a 1-hour window.
- Gemini API latency exceeds 5 seconds (indicating potential quota issues).

## 4. Troubleshooting Runbook
- **Missing Chunks (Hit Rate Drop)**: Verify `data/chroma_db` is intact and not corrupted. Re-run `ingest_data.py` locally and push.
- **Gemini API Fails (Fallback Triggered)**: Check `GEMINI_API_KEY` quota and billing in Google AI Studio. The app will continue to function deterministically.
- **App Crash on Startup**: Ensure `sentence-transformers` models can be downloaded (requires outbound internet access from the host).

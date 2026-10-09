# Deployment Instructions (Streamlit Community Cloud)

This project is fully prepared for deployment on **Streamlit Community Cloud**.

## 1. Prerequisites
- The project must be pushed to a public or private GitHub repository.
- Ensure that `data/chroma_db/` and `data/processed/` are committed to the repository. These contain the pre-computed Vector Embeddings and BM25 index. They are lightweight enough for a portfolio project.
- Do NOT commit `.env`.

## 2. Deployment Steps
1. Log in to [Streamlit Community Cloud](https://share.streamlit.io/).
2. Click **New app**.
3. Select your GitHub repository, branch, and set the Main file path to `app.py`.
4. Click **Advanced settings** (this is critical!).

## 3. Environment Variables (Advanced Settings)
Under the **Secrets** section in Advanced settings, paste the following (replace with your real keys):

```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
LANGSMITH_TRACING = "true"
LANGSMITH_API_KEY = "your_langsmith_api_key_here"
LANGSMITH_PROJECT = "siliconsense-rag"
```

*Note: The Gemini API key is optional. If missing or invalid, the app will gracefully fall back to deterministic Python summaries.*

## 4. Cold Start & Resource Limits
- **Dependencies**: Streamlit Cloud will automatically install dependencies from `requirements.txt`.
- **Models**: The `sentence-transformers` and `flashrank` models will be downloaded into the ephemeral instance cache on the first run (cold start). The first query may take 10-15 seconds longer than usual.
- **Resource Constraints**: Streamlit Cloud provides ~1GB RAM. The models chosen (`MiniLM-L6-v2` and `ms-marco-MiniLM-L-12-v2`) are extremely lightweight and fit comfortably in this memory limit.

## 5. Monitoring
Once deployed:
- **Streamlit Analytics**: Accessible via the Streamlit dashboard for basic request tracking.
- **LangSmith**: All queries, retriever latencies, and Gemini explanations will automatically stream to your LangSmith project for advanced observability and evaluation.

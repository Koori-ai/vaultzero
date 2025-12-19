# Use Python 3.11 slim for smaller image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# PERFORMANCE FIX: Pre-download dataset during build (not at runtime!)
# This eliminates the HuggingFace download on every startup
RUN mkdir -p /app/data && \
    python -c "from huggingface_hub import hf_hub_download; \
    hf_hub_download(\
        repo_id='Reply2susi/zero-trust-maturity-assessments', \
        filename='zt_synthetic_dataset_complete.json', \
        repo_type='dataset', \
        local_dir='/app/data'\
    )" || echo "Dataset download during build failed, will retry at runtime"

# PERFORMANCE FIX: Pre-initialize ChromaDB during build
# This creates the vector database ahead of time
RUN python -c "import os; \
os.makedirs('/app/data/chroma_db', exist_ok=True); \
try: \
    from rag.vectorstore import VaultZeroRAG; \
    rag = VaultZeroRAG(data_path='/app/data/zt_synthetic_dataset_complete.json', persist_directory='/app/data/chroma_db'); \
    rag.initialize(); \
    print('✅ RAG initialized during build!'); \
except Exception as e: \
    print(f'⚠️ RAG init skipped: {e}');" || echo "RAG init during build failed, will init at runtime"

# Expose port 8080 for Cloud Run
EXPOSE 8080

# Set environment variables for Streamlit
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]

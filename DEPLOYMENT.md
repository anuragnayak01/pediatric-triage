# Deployment Guide – Pediatric Safety Triage

Complete instructions for deploying the Pediatric Safety Triage system in local, Docker, or cloud environments.

---

## Prerequisites

- **Python 3.9+** (tested on 3.11)
- **pip** or **conda**
- **4GB RAM minimum** (embeddings + ChromaDB index)
- **2GB disk space** (knowledge base + indexes)
- **OS:** Linux, macOS, or Windows (with PowerShell or WSL)

---

## Option 1: Local Development (Fastest)

### Step 1: Clone & Setup Environment

```bash
# Navigate to project
cd /path/to/Technical_Assessment

# Create virtual environment
python -m venv .venv

# Activate
# On Linux/macOS:
source .venv/bin/activate
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Windows CMD:
.venv\Scripts\activate.bat
```

### Step 2: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**First-time setup takes 2–3 minutes** (downloads multilingual embeddings ~400MB).

### Step 3: Run the Application

```bash
# Start Streamlit UI
streamlit run app.py

# Console output:
# You can now view your Streamlit app in your browser.
# Local URL: http://localhost:8501
```

Open browser to `http://localhost:8501`

### Step 4: Verify Installation

```bash
# Run evaluation suite (should show 15/17 passing)
python eval.py

# Output:
# Total tests: 17
# Passed: 15
# Failed: 2
# Results saved to: eval_sources/results.json
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'streamlit'` | Run `pip install -r requirements.txt` |
| `CUDA out of memory` | Sentence-transformers falls back to CPU (slower but works) |
| `Port 8501 already in use` | Kill process: `lsof -ti:8501 \| xargs kill -9` (Linux/macOS) or use `streamlit run app.py --server.port 8502` |
| `Permission denied: .venv/bin/activate` | Run `chmod +x .venv/bin/activate` (Linux/macOS) |
| ChromaDB index not found on first run | Expected – will auto-build on first startup (~2–3 min) |

---

## Option 2: Docker Deployment

### Step 1: Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Step 2: Build Docker Image

```bash
# Build (first time ~3–5 min with embedding downloads)
docker build -t pediatric-triage:v1.0 .

# Verify
docker images | grep pediatric-triage
```

### Step 3: Run Container

```bash
# Run detached
docker run -d \
  --name pediatric-triage \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  pediatric-triage:v1.0

# Check logs
docker logs pediatric-triage

# Stop
docker stop pediatric-triage
docker rm pediatric-triage
```

### Step 4: Verify

- Open `http://localhost:8501`
- Test with sample input
- Check logs: `docker logs pediatric-triage`

### Docker Compose (Optional – Multi-Service Setup)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - ./data:/app/data
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

Run:
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

---

## Option 3: Streamlit Cloud Deployment (Free, Public)

### Prerequisites
- GitHub account
- Code pushed to GitHub public repo

### Step 1: Push to GitHub

```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: Pediatric Triage System"
git remote add origin https://github.com/YOUR_USER/pediatric-triage.git
git push -u origin main
```

### Step 2: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Select repo, branch (`main`), and main file (`app.py`)
5. Deploy

**URL:** `https://share.streamlit.io/YOUR_USER/pediatric-triage/main/app.py`

### Step 3: Auto-Deploy

- **On push:** App auto-rebuilds on each commit to `main` branch
- **Monitor:** Check deploy status in Streamlit Cloud dashboard

### Limitations
- Streamlit Cloud has session timeout (15 min inactivity)
- Cold starts may take 1–2 min on first load
- Resource limits: 1GB RAM, 2GB disk

---

## Option 4: AWS Deployment (Advanced)

### Using AWS Elastic Container Service (ECS)

1. **Build & Push Docker Image to ECR**
```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com
docker tag pediatric-triage:v1.0 ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pediatric-triage:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/pediatric-triage:latest
```

2. **Create ECS Task Definition** (use Dockerfile above)

3. **Launch ECS Service** on Fargate (serverless)

4. **Expose via Application Load Balancer (ALB)**

5. **Monitor with CloudWatch**

---

## Performance Tuning

### Reduce Startup Time

1. **Pre-build embeddings locally:**
```bash
python -c "from sentence_transformers import SentenceTransformer; m = SentenceTransformer('intfloat/multilingual-e5-base'); print('Downloaded')"
```

2. **Bake into Docker image** (modify Dockerfile):
```dockerfile
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('intfloat/multilingual-e5-base')"
```

3. **Use persistent volume for ChromaDB:**
```bash
docker run -v /persistent/data:/app/data ...
```

### Improve Query Speed

- ChromaDB caches embeddings in memory (first query slower, subsequents <100ms)
- Reduce `max_context_chunks` in `src/retrieval.py` if needed (default: 4)
- Use GPU if available (auto-detected by sentence-transformers)

### Monitor Resource Usage

```bash
# Docker stats
docker stats pediatric-triage

# Process memory (local)
ps aux | grep "streamlit\|python"

# Logs
docker logs pediatric-triage
streamlit run app.py --logger.level=debug
```

---

## Production Checklist

- ✅ Evaluation tests passing (15/17, 88%)
- ✅ Schema validation enabled
- ✅ Knowledge base ingested (410 chunks)
- ✅ Safety guardrails active
- ✅ Multilingual support verified (EN/AR)
- ✅ No API keys required
- ⏳ Add `.env` configuration (optional)
- ⏳ Add logging/monitoring (optional)
- ⏳ Add rate limiting for API gateway (if exposing via API)
- ⏳ Add SSL/TLS certificate (if on public domain)

---

## Monitoring & Logging

### Local Development
```bash
# Enable debug logging
streamlit run app.py --logger.level=debug

# View logs in browser (Streamlit UI bottom-right menu)
```

### Docker Deployment
```bash
# View logs
docker logs pediatric-triage

# Follow logs in real-time
docker logs -f pediatric-triage

# Export logs
docker logs pediatric-triage > app.log 2>&1
```

### Application Metrics

See `eval_sources/results.json` for evaluation metrics:
```bash
# View results
cat eval_sources/results.json | python -m json.tool
```

---

## Troubleshooting

| Error | Root Cause | Solution |
|-------|-----------|----------|
| `ConnectionError: Failed to connect to ChromaDB` | Index corrupted or missing | Delete `data/indexes/chroma/` and restart (rebuilds on startup) |
| `OutOfMemory error` | Embeddings too large | Reduce batch size in `src/retrieval.py` or add swap |
| `Slow query response` | First query of session | Expected (~500ms first, <100ms subsequent) |
| `Invalid temperature reading` | Out of bounds (35–107°F) | UI validation prevents this; check input logic |
| `Language detection fails` | Unclear or mixed text | System defaults to English; user can override |
| `404 on Streamlit Cloud` | Build failed or dependencies missing | Check `streamlit.log` in Streamlit Cloud dashboard |

---

## Rollback & Downtime Prevention

### Local/Docker
```bash
# Keep previous version running on different port
streamlit run app.py --server.port 8502

# Test new version on 8502, then switch traffic
```

### Streamlit Cloud
```bash
# Revert to previous commit
git revert <commit_hash>
git push origin main
# App auto-redeploys from GitHub
```

### Docker with Blue-Green Deployment
```bash
# Run current version (blue)
docker run -d --name app-blue -p 8501:8501 pediatric-triage:v1.0

# Deploy new version (green) on different port
docker run -d --name app-green -p 8502:8501 pediatric-triage:v2.0

# Test green, then switch traffic
docker stop app-blue
docker rename app-green app-blue
```

---

## Support & Documentation

- **Main README:** [README.md](README.md) – Quick start, features, evaluation results
- **Implementation docs:** See [docs/](docs/) folder
- **Evaluation results:** [eval_sources/results.json](eval_sources/results.json)
- **Architecture audit:** [docs/RAG_COMPLIANCE_AUDIT.md](docs/RAG_COMPLIANCE_AUDIT.md)

---

## Next Steps

1. Choose deployment option (local recommended for first run)
2. Follow setup steps
3. Verify with `python eval.py`
4. Share feedback or extend system
5. Monitor performance in production

Happy deploying! 🚀

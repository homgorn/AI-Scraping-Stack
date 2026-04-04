# Getting Started

> Get AI Scraping Stack running in 5 minutes. No prior experience needed.

## Prerequisites

- **Python 3.11+** — [Download Python](https://www.python.org/downloads/)
- **Git** — [Install Git](https://git-scm.com/downloads)
- **Ollama** (optional, for local AI) — [Install Ollama](https://ollama.ai)

## Step 1: Clone the Repository

```bash
git clone https://github.com/homgorn/ai-scraping-stack.git
cd ai-scraping-stack
```

## Step 2: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows

# Install all dependencies
pip install -r requirements.txt

# Install Scrapling browsers
scrapling install
```

## Step 3: Configure Environment

```bash
# Copy the example config
cp .env.example .env

# Open .env in your editor
# At minimum, set these (everything works without keys):
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

### Optional: Add API Keys for Better Results

```env
# OpenRouter — 300+ cloud models (free tier available)
# Get key: openrouter.ai/keys
OPENROUTER_API_KEY=sk-or-v1-...

# Jina Reader — higher rate limit with key
# Get key: jina.ai
JINA_API_KEY=jina_...
```

## Step 4: Install Local AI Models (Optional)

```bash
# Base model for text analysis
ollama pull llama3.2

# Vision models for screenshot analysis
ollama pull qwen2.5vl:7b   # Best quality
ollama pull moondream       # Fast, runs on CPU
```

## Step 5: Run Health Check

```bash
python debug.py --full
```

Expected output:
```
✓ Config loads: .env parsed successfully
✓ ollama_host: http://localhost:11434
✓ Ollama server: online
✓ Scrapling: installed
```

## Step 6: Start the Server

```bash
uvicorn api:app --reload --port 8100
```

Server is now running at **http://localhost:8100**

## Step 7: Open the Dashboard

Open `landing.html` in your browser, or visit:
- **http://localhost:8100/docs** — Interactive API docs (Swagger)
- **landing.html** — Full dashboard UI

## Verify It Works

```bash
# Test the health endpoint
curl http://localhost:8100/
# → {"status":"ok","version":"1.0.0"}

# Test a simple scrape
curl -X POST http://localhost:8100/scrape \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","strategy":"free","task":"summarize"}'
```

## Next Steps

- Read the [Architecture](Architecture) guide to understand the system
- Explore the [API Reference](API-Reference) for all endpoints
- Check [Deployment](Deployment) to put it online
- See [Contributing](Contributing) to help improve the project

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: scrapling` | Run `pip install -r requirements.txt` |
| Ollama not responding | Run `ollama serve` |
| Port 8100 in use | Use `--port 8101` or kill the other process |
| `data/` directory missing | Run `mkdir -p data` |

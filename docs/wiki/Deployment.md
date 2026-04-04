# Deployment

> Step-by-step guides to deploy AI Scraping Stack to various platforms.

## Overview

AI Scraping Stack consists of two parts that can be deployed separately:

```
┌─────────────────────┐     fetch()      ┌──────────────────┐
│ Frontend (Static)   │ ───────────────→  │ Backend (API)    │
│ landing.html        │   POST /scrape    │ FastAPI (Python) │
│ GitHub Pages / CF   │   POST /synthesize│ Render / Railway │
└─────────────────────┘ ←────────────────┘                  │
                     JSON response         └──────────────────┘
```

---

## Backend Deployment

### Option 1: Render.com (Free)

**Best for:** Quick deployment, no credit card needed.

1. Go to [render.com](https://render.com) → Sign Up via GitHub
2. Click **New +** → **Web Service**
3. Select your repo `ai-scraping-stack`
4. Fill in:
   - **Name:** `ai-scraping-stack`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn api:app --host 0.0.0.0 --port $PORT`
   - **Instance Type:** **Free**
5. Add Environment Variables:
   - `OPENROUTER_API_KEY=sk-or-v1-...`
   - `API_KEY=your-secret-key` (for protection)
   - Other keys from `.env.example`
6. Click **Create Web Service**

Your API will be available at: `https://ai-scraping-stack.onrender.com`

**Note:** Free tier sleeps after 15 minutes of inactivity. Use the `keep-alive.yml` GitHub Action to ping every 10 minutes.

### Option 2: Railway.app

**Best for:** More resources, $5 free credits/month.

1. Go to [railway.app](https://railway.app) → Sign Up via GitHub
2. **New Project** → **Deploy from GitHub repo**
3. Select `ai-scraping-stack`
4. Add environment variables in Railway dashboard
5. Railway auto-detects `Dockerfile` and builds

### Option 3: Timeweb Cloud (with GPU for Ollama)

**Best for:** Full control, local AI models, Russian hosting.

See [DEPLOY_TIMEWEB.md](../DEPLOY_TIMEWEB.md) for detailed instructions including:
- GPU server setup
- Ollama installation
- Nginx reverse proxy
- systemd service
- SSL with Let's Encrypt

### Option 4: Docker

```bash
# Build
docker build -t ai-scraping-stack .

# Run
docker run -p 8100:8100 \
  -e OPENROUTER_API_KEY=sk-or-v1-... \
  -e API_KEY=your-secret-key \
  ai-scraping-stack

# Or with docker-compose
docker-compose up -d
```

---

## Frontend Deployment

### Option 1: GitHub Pages (Free)

1. Go to repo **Settings** → **Pages**
2. **Source:** Deploy from a branch
3. **Branch:** `main`, folder: `/ (root)`
4. Your site will be at: `https://homgorn.github.io/ai-scraping-stack/landing.html`

### Option 2: Cloudflare Pages (Free)

1. Go to [pages.cloudflare.com](https://pages.cloudflare.com)
2. Connect GitHub repo
3. Build settings: none needed (static HTML)
4. Deploy

### Option 3: Netlify (Free)

1. Drag and drop the folder to [app.netlify.com/drop](https://app.netlify.com/drop)
2. Or connect GitHub repo

---

## Configuration After Deploy

### 1. Update API_URL in landing.html

Open `landing.html` and set:
```javascript
const API_URL = 'https://your-api.onrender.com';
const API_KEY = 'your-secret-key'; // Same as API_KEY in Render
```

### 2. Add GitHub Secret for Keep-Alive

1. Repo **Settings** → **Secrets and variables** → **Actions**
2. **New repository secret**
3. **Name:** `RENDER_API_URL`
4. **Value:** `https://your-api.onrender.com`

### 3. Set Environment Variables in Render

| Variable | Example | Required |
|----------|---------|----------|
| `OPENROUTER_API_KEY` | `sk-or-v1-...` | For cloud LLMs |
| `API_KEY` | `MySecret_2026!` | For API protection |
| `JINA_API_KEY` | `jina_...` | For higher rate limit |
| `OLLAMA_HOST` | `http://localhost:11434` | Only if Ollama is running |
| `DB_PATH` | `/app/data/scrapling.db` | For persistent storage |

---

## Security Checklist

- [ ] `API_KEY` set in Render Environment Variables
- [ ] `API_KEY` set in `landing.html` (same value)
- [ ] CORS restricted to your domain (not `*`)
- [ ] HTTPS enabled (automatic on Render/GitHub Pages)
- [ ] `.env` file NOT committed to git
- [ ] Rate limiting enabled (default: 10 req/min)
- [ ] Keep-alive workflow configured

## Monitoring

- **Render Logs:** Dashboard → your service → **Logs** tab
- **GitHub Actions:** Actions tab → `keep-alive` workflow runs
- **API Health:** `GET /status` endpoint
- **Analytics:** Plausible/Umami script in `landing.html`

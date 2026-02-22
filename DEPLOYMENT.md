# 🚀 DocuMind AI — Deployment Guide

## Complete step-by-step to deploy both Backend + Frontend for FREE.

---

## Prerequisites

1. **GitHub account** → https://github.com
2. **Railway account** → https://railway.app (sign up with GitHub)
3. **Vercel account** → https://vercel.com (sign up with GitHub)
4. **Groq API key** → https://console.groq.com (free)

---

## Step 1: Initialize Git & Push to GitHub

```bash
# Navigate to project
cd ~/Upwork\ Profile/DocuMind-AI

# Initialize git
git init
git add .
git commit -m "Initial commit: DocuMind AI - Enterprise RAG Platform"

# Create repo on GitHub (via browser or gh CLI):
# Go to https://github.com/new → name it "DocuMind-AI" → Create

# Connect and push
git remote add origin https://github.com/YOUR_USERNAME/DocuMind-AI.git
git branch -M main
git push -u origin main
```

---

## Step 2: Deploy Backend → Railway (FREE)

### 2a. Create Railway Project

1. Go to https://railway.app/new
2. Click **"Deploy from GitHub Repo"**
3. Select your **DocuMind-AI** repository
4. Railway auto-detects the Dockerfile

### 2b. Configure Environment Variables

In Railway dashboard → your service → **Variables** tab → add:

```
GROQ_API_KEY=gsk_your_actual_groq_key_here
LLM_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./data/chroma_db
UPLOAD_DIR=./data/uploads
DATABASE_URL=sqlite:///./data/documind.db
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
```

### 2c. Configure Settings

In Railway → **Settings** tab:
- **Root Directory:** `/` (leave default)
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Port:** Railway auto-assigns (uses `$PORT`)

> ⚠️ Railway uses dynamic ports. Update the start command to use `$PORT`:

### 2d. Update Backend for Railway's Dynamic Port

Railway assigns a random port via `$PORT` env var. The app needs to respect this.

### 2e. Get Your Backend URL

Once deployed, Railway gives you a URL like:
```
https://documind-ai-production.up.railway.app
```

**Copy this URL** — you'll need it for the frontend.

### 2f. Test Backend

Open in browser:
```
https://YOUR-BACKEND-URL.railway.app/docs
```
You should see the FastAPI Swagger docs.

---

## Step 3: Deploy Frontend → Vercel (FREE)

### 3a. Create Vercel Project

1. Go to https://vercel.com/new
2. Click **"Import Git Repository"**
3. Select your **DocuMind-AI** repository

### 3b. Configure Build Settings

In the Vercel import screen:
- **Framework Preset:** Vite
- **Root Directory:** `frontend`
- **Build Command:** `npm run build`
- **Output Directory:** `dist`

### 3c. Add Environment Variable

In Vercel → **Environment Variables** section:

```
VITE_API_URL = https://YOUR-BACKEND-URL.railway.app/api/v1
```

Replace `YOUR-BACKEND-URL` with your actual Railway URL from Step 2e.

### 3d. Deploy

Click **"Deploy"** — Vercel builds and deploys automatically.

Your frontend URL will be:
```
https://documind-ai.vercel.app
```

---

## Step 4: Connect & Verify

1. **Open your Vercel URL** in browser
2. Go to **Settings** page → check that services show "connected"
3. Go to **Documents** → upload a PDF
4. Go to **Chat** → ask a question about the uploaded document
5. Check **Analytics** → verify queries are being tracked

---

## Step 5: Update Backend CORS (if needed)

If you get CORS errors, update `app/main.py` to allow your Vercel domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://documind-ai.vercel.app",  # Add your Vercel URL
        "https://*.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

Then commit and push — Railway auto-redeploys.

---

## Auto-Deploy (CI/CD)

Both Railway and Vercel auto-deploy on every `git push`:

```bash
# Make a change, then:
git add .
git commit -m "update: description of change"
git push

# Both Railway (backend) and Vercel (frontend) auto-redeploy!
```

---

## Quick Reference

| Component | Platform | URL | Cost |
|-----------|----------|-----|------|
| Backend | Railway | `https://YOUR-APP.railway.app` | $0 (free tier) |
| Frontend | Vercel | `https://YOUR-APP.vercel.app` | $0 (free tier) |
| API Docs | Railway | `https://YOUR-APP.railway.app/docs` | — |
| LLM | Groq | API calls | $0 (free tier) |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| CORS error | Add your Vercel URL to CORS origins in `main.py` |
| API not connecting | Check `VITE_API_URL` in Vercel env vars matches Railway URL |
| LLM not working | Verify `GROQ_API_KEY` is set in Railway env vars |
| File upload fails | Check Railway has writable `/data` directory |
| Embeddings slow on first load | Normal — model downloads on first request (~100MB) |

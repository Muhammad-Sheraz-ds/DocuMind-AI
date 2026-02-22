---
title: DocuMind AI
emoji: 📚
colorFrom: purple
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
short_description: Enterprise RAG Platform — AI Document Q&A with Citations
---

# 📚 DocuMind AI — Enterprise RAG Platform

> Upload documents. Ask questions. Get AI answers with citations. Measure accuracy. Track analytics.

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green?style=flat-square&logo=fastapi)
![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3-orange?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📄 **Multi-Format Ingestion** | Upload PDF, DOCX, TXT, CSV, MD — auto-parsed and chunked |
| 🔍 **Hybrid Search** | Semantic embeddings + BM25 keyword search + Reciprocal Rank Fusion |
| 💬 **AI Chat with Citations** | Ask questions, get grounded answers with source references |
| 🛡️ **Guardrails** | Prompt injection detection (13 patterns), PII flagging, output grounding |
| 📊 **Analytics Dashboard** | Usage stats, query trends, retrieval scores, user feedback |
| 🧪 **Evaluation Harness** | Golden Q&A test sets, retrieval accuracy, answer faithfulness |
| ⚡ **100% Free Stack** | Groq (free tier), HuggingFace (local), ChromaDB, SQLite |

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Streamlit   │────→│   FastAPI    │────→│   Groq API   │
│  Frontend    │     │   Backend    │     │  (Llama 3.3) │
└──────────────┘     └──────┬───────┘     └──────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ ChromaDB │ │  SQLite  │ │HuggingFace│
        │ (vectors)│ │  (logs)  │ │(embeddings)│
        └──────────┘ └──────────┘ └──────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/DocuMind-AI.git
cd DocuMind-AI
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your Groq API key
# Get free key at: https://console.groq.com
```

### 3. Run Backend

```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Run Frontend (new terminal)

```bash
cd frontend
npm install
npm run dev
```

### 5. Open

- **Frontend:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 🐳 Docker

```bash
docker-compose up --build
```

---

## 📁 Project Structure

```
DocuMind-AI/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py             # Environment configuration
│   ├── models/
│   │   ├── database.py       # SQLAlchemy models
│   │   └── schemas.py        # Pydantic request/response models
│   ├── services/
│   │   ├── ingestion.py      # Document parsing & chunking
│   │   ├── embedding.py      # HuggingFace sentence-transformers
│   │   ├── retrieval.py      # Hybrid search (semantic + BM25 + RRF)
│   │   ├── llm.py            # Groq API (Llama 3.3 70B)
│   │   ├── guardrails.py     # Prompt injection + PII detection
│   │   └── evaluation.py     # Golden Q&A evaluation harness
│   └── api/
│       └── routes.py         # API endpoints
├── frontend/                 # React + Vite
│   └── src/
│       ├── App.jsx           # Main app component
│       ├── index.css          # Design system (dark theme)
│       ├── services/api.js   # Axios API client
│       ├── components/
│       │   └── Sidebar.jsx   # Navigation sidebar
│       └── pages/
│           ├── ChatPage.jsx       # Chat with citations
│           ├── DocumentsPage.jsx  # Upload & manage docs
│           ├── AnalyticsPage.jsx  # Usage dashboard
│           ├── EvaluationPage.jsx # Golden Q&A harness
│           └── SettingsPage.jsx   # System config
├── data/                     # Uploads + ChromaDB + SQLite
├── .env.example
├── requirements.txt
├── Dockerfile / docker-compose.yml
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/upload` | Upload & index a document |
| `POST` | `/api/v1/ask` | Ask a question (RAG) |
| `GET` | `/api/v1/documents` | List uploaded documents |
| `DELETE` | `/api/v1/documents/{id}` | Delete a document |
| `POST` | `/api/v1/evaluate` | Run evaluation harness |
| `GET` | `/api/v1/evaluate/history` | Past evaluation results |
| `GET` | `/api/v1/analytics` | Usage analytics |
| `POST` | `/api/v1/feedback` | Submit query feedback |

---

## 🛡️ Security Features

- **Prompt Injection Detection** — 13 regex patterns for common injection attacks
- **PII Flagging** — Detects emails, phone numbers, SSNs, credit cards
- **Output Grounding** — Validates LLM answers are based on context, not hallucinated
- **Input Sanitization** — Length limits, encoded content detection
- **No Data Leakage** — Client documents stored locally, never sent to training

---

## 🧪 Evaluation

Run accuracy tests with golden Q&A pairs:

```python
import httpx

response = httpx.post("http://localhost:8000/api/v1/evaluate", json={
    "test_name": "my_test",
    "questions": [
        {
            "question": "What is the company's revenue?",
            "expected_answer": "The company's revenue was $10M in 2024."
        }
    ]
})
print(response.json())
```

---

## ⚙️ Tech Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| LLM | Groq (Llama 3.3 70B Versatile) | 🆓 Free tier |
| Embeddings | HuggingFace sentence-transformers | 🆓 Local |
| Vector DB | ChromaDB | 🆓 Open source |
| Database | SQLite (SQLAlchemy) | 🆓 Built-in |
| Backend | FastAPI + Uvicorn | 🆓 Open source |
| Frontend | React + Vite | 🆓 Open source |
| Deploy | Docker / Vercel + Railway | 🆓 Free tiers |

**Total cost: $0/month** 🎉

---

## 📄 License

MIT License — use freely for commercial and personal projects.

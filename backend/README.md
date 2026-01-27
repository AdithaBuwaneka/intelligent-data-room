---
title: Intelligent Data Room
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
app_file: app/main.py
pinned: false
---

# Intelligent Data Room API

FastAPI backend with multi-agent AI system using LangGraph and PandasAI.

## 🏗️ Architecture

```
POST /api/query
     ↓
Classifier → Data Question? → Planner Agent → Executor Agent → Response
     ↓                              ↓               ↓
  Greeting?                   Google Gemini    PandasAI + Gemini
     ↓
Friendly Response
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload` | POST | Upload CSV/XLSX file |
| `/api/query` | POST | Send query to AI agents |
| `/api/history/{id}` | GET | Get chat history |
| `/api/sessions` | GET | List all sessions |
| `/health` | GET | Health check |

## 🤖 Agent System

1. **Classifier** - Detects greetings vs data questions
2. **Planner** - Creates step-by-step execution plan
3. **Executor** - Runs PandasAI code, generates charts

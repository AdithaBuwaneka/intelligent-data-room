# Backend - Intelligent Data Room API

FastAPI backend with multi-agent AI system using LangGraph and PandasAI.

## 🌐 Live API

[huggingface.co/spaces/adithaf7/intelligent-data-room](https://huggingface.co/spaces/adithaf7/intelligent-data-room)

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

## 🚀 Local Setup

```bash
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

## 🔧 Environment Variables

```env
GEMINI_API_KEY=your_gemini_api_key
MONGODB_URI=your_mongodb_connection_string
IMAGEKIT_PRIVATE_KEY=your_imagekit_private_key
IMAGEKIT_PUBLIC_KEY=your_imagekit_public_key
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_id
```

## 📁 Structure

```
app/
├── agents/         # Planner, Executor, Classifier
├── graph/          # LangGraph workflow
├── routers/        # API routes (upload, query)
├── services/       # Database, ImageKit, Memory
├── models/         # Pydantic schemas
└── main.py         # FastAPI app
```

## 🤖 Agent System

1. **Classifier** - Detects greetings vs data questions
2. **Planner** - Creates step-by-step execution plan
3. **Executor** - Runs PandasAI code, generates charts

---
title: Intelligent Data Room API
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
sdk_version: "4.36.0"
python_version: "3.11"
app_port: 7860
pinned: false
license: mit
---

# 📊 Intelligent Data Room

AI-powered data analysis platform with multi-agent architecture. Upload CSV/XLSX files and chat with your data using natural language.

## 🔗 Quick Links

- **Live Demo:** [intelligent-data-room.vercel.app](https://intelligent-data-room.vercel.app)
- **Backend API:** [adithaf7-intelligent-data-room.hf.space](https://adithaf7-intelligent-data-room.hf.space)
- **Health Check:** [adithaf7-intelligent-data-room.hf.space/health](https://adithaf7-intelligent-data-room.hf.space/health)
- **GitHub Repo:** [github.com/AdithaBuwaneka/intelligent-data-room](https://github.com/AdithaBuwaneka/intelligent-data-room)
- **GitHub Actions:** [View CI/CD Workflows](https://github.com/AdithaBuwaneka/intelligent-data-room/actions)

**📚 Deployment Guides:**
- [Deploy to Hugging Face Spaces (Backend)](README_HUGGINGFACE.md)
- [MongoDB Atlas Setup Guide](MONGODB_SETUP.md)
- [Deployment Checklist](HF_DEPLOYMENT_CHECKLIST.md)

---

## 🎯 Features

- **Multi-Agent System:** Planner (Gemini 2.5 Flash) creates execution plans → Executor (PandasAI) generates Python code and results
- **Intelligent Query Analysis:** QueryAnalyzer validates queries, extracts parameters (limit, columns, aggregation), and detects follow-ups
- **Smart Classification:** Distinguishes greetings, chitchat, and data questions using semantic understanding
- **Auto-Visualization:** Generates charts (bar, line, pie, scatter, area) intelligently based on query intent
- **Context Memory:** Retains last 5 messages for seamless follow-up questions
- **Follow-up Detection:** Handles "as pie chart", "top 10 instead", "just west region" intelligently
- **Session Persistence:** Files and chats survive page refresh via MongoDB

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              React Frontend (Vercel)                        │
│       FileUpload • ChatInterface • ChartDisplay             │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTPS
┌─────────────────────────▼───────────────────────────────────┐
│              FastAPI Backend (Hugging Face Spaces)          │
│         /upload • /query • /history • /sessions             │
└─────────────────────────┬───────────────────────────────────┘
                          │
         ┌────────────────▼────────────────┐
         │      1. Memory Service          │◄────────────────┐
         │   (Load last 5 messages)        │                 │
         └────────────────┬────────────────┘                 │
                          │                                  │
         ┌────────────────▼────────────────┐                 │
         │      2. Query Classifier        │                 │
         │      (Gemini 2.5 Flash)         │                 │
         └───────┬────────────────┬────────┘                 │
                 │                │                          │
        [Greeting/Chitchat]  [Data Question]                 │
                 │                │                          │
                 │          ┌─────▼──────┐                   │
                 │          │ Load Data  │                   │
                 │          │ (ImageKit) │                   │
                 │          └─────┬──────┘                   │
                 │                │                          │
                 │   ┌────────────▼────────────┐             │
                 │   │    3. Query Analyzer    │             │
                 │   │    (Gemini 2.5 Flash)   │             │
                 │   │  • is_meaningful_query? │             │
                 │   │  • can_be_answered?     │             │
                 │   │  • detect follow-ups    │             │
                 │   └─────┬─────────────┬─────┘             │
                 │         │             │                   │
                 │    [Valid Query]  [Invalid]               │
                 │         │             │                   │
                 │         │             ▼                   │
                 │         │    Save + Return Error ─────────┤
                 │         │                                 │
                 │   ┌─────▼─────────────────┐               │
                 │   │  4. LangGraph Workflow │               │
                 │   │ ┌────────┐ ┌────────┐ │               │
                 │   │ │Planner │►│Executor│ │               │
                 │   │ │(Gemini)│ │(Pandas │ │               │
                 │   │ └────────┘ │AI+Gem) │ │               │
                 │   │            └────────┘ │               │
                 │   └───────────┬───────────┘               │
                 │               │                           │
                 │   ┌───────────▼───────────┐               │
                 └──►│   5. Save to MongoDB  │───────────────┘
                     │ (Messages+Analysis)   │
                     └───────────┬───────────┘
                                 │
                                 ▼
                          Return Response
                       (answer + chart_config)

External Services:
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   MongoDB    │  │   ImageKit   │  │ Google Gemini│
│   Atlas      │  │     CDN      │  │     API      │
│  (History)   │  │   (Files)    │  │   (AI/LLM)   │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 🛠️ Tech Stack

**Backend:** FastAPI • Gemini 2.5 Flash • LangGraph • PandasAI • MongoDB Atlas • ImageKit  
**Frontend:** React + TypeScript • Vite • TailwindCSS • Recharts  
**Deployment:** Vercel (Frontend) • Hugging Face Spaces (Backend)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- **Google Gemini API Key** → [Get from Google AI Studio](https://aistudio.google.com/apikey)
- **MongoDB Atlas URI** → [Setup Guide](MONGODB_SETUP.md) or [MongoDB Atlas](https://www.mongodb.com/atlas)
- **ImageKit credentials** → [Get from ImageKit.io](https://imagekit.io/)

### 1. Clone Repository
```bash
git clone https://github.com/AdithaBuwaneka/intelligent-data-room.git
cd intelligent-data-room
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` file in `backend/` folder:
```env
GEMINI_API_KEY=your-gemini-api-key
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority
IMAGEKIT_PUBLIC_KEY=your-public-key
IMAGEKIT_PRIVATE_KEY=your-private-key
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your-id
```

Run backend server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Backend runs at: http://localhost:8000

### 3. Frontend Setup
```bash
cd frontend
npm install
```

Create `.env` file in `frontend/` folder:
```env
VITE_API_URL=http://localhost:8000
```

Run frontend:
```bash
npm run dev
```
Frontend runs at: http://localhost:5173

---

## 📂 Project Structure

```
intelligent-data-room/
├── backend/app/
│   ├── agents/              # classifier.py, planner.py, executor.py, query_analyzer.py
│   ├── graph/               # workflow.py (LangGraph orchestration)
│   ├── routers/             # upload.py, query.py (FastAPI endpoints)
│   ├── services/            # database.py, memory.py, imagekit_service.py
│   ├── models/schemas.py    # Pydantic models
│   └── main.py              # FastAPI app entry
├── frontend/src/
│   ├── components/          # FileUpload, ChatInterface, MessageList, ChartDisplay, LoadingSpinner
│   ├── hooks/               # useChat.ts, useFileUpload.ts
│   ├── services/api.ts      # API client
│   ├── types/               # TypeScript type definitions
│   └── App.tsx              # Main component
```

---

## 💡 Sample Queries

**Basic Analysis:**
```
"Show total sales by category"
"Top 5 states by sales"
"Create a pie chart of sales by region"
```

**Advanced Queries:**
```
"How has profit changed over the years? Use a line chart"
"Is there a correlation between Discount and Profit? Create a scatter plot"
"Compare sales trend of different ship modes over time"
```

**Smart Follow-ups:**
```
User: "Show top 10 customers by profit"
AI: [Returns bar chart with top 10]
User: "as pie chart"
AI: [Same data, now as pie chart]
User: "just 5"
AI: [Top 5 customers as pie chart]
User: "only west region"
AI: [Top 5 west region customers as pie chart]
```

**Context Awareness:**
```
"hi" or "how are you"
→ Responds conversationally without triggering data analysis

"Calculate Return Rate by Region"
→ AI explains dataset lacks return data and suggests alternatives
```

> **📝 Note on Test Prompt #10:** The challenge includes "Calculate Return Rate" but the Sample Superstore.csv doesn't contain return/refund data. The AI correctly identifies this limitation and explains what data would be needed. This demonstrates intelligent error handling.

---

## 🔑 Key Technical Features

**1. Intelligent Classification**
- Semantic understanding using Gemini 2.5 Flash (no keyword matching)
- Handles ANY phrasing, typos, slang, multiple languages
- Context-aware: distinguishes greetings vs. follow-up questions

**2. Query Analysis & Validation**
- Validates queries before expensive processing (filters gibberish like "pp", "test")
- Extracts parameters: limit_number, group_column, value_column, aggregation
- Detects follow-up types: chart_type_change, limit_change, column_change, filter_change
- Fuzzy column matching with synonym support (sales=revenue, profit=earnings)

**3. Smart Visualization**
- Intent-based: AI decides if charts add value (not keyword matching)
- Supports 5 chart types: bar, line, pie, scatter, area
- Respects user preferences ("don't chart", "without graph")

**4. Multi-Agent Workflow**
- Planner: Analyzes question + schema → Creates execution plan
- Executor: PandasAI generates Python → Executes → Returns results
- Fallback to Gemini API on PandasAI failures

**5. Context Management**
- MongoDB stores conversation history per session
- Last 5 messages used for follow-up detection
- Previous query analysis inherited for follow-ups
- Session persistence across page refreshes

---

## 📊 API Endpoints

```
POST   /api/upload                    # Upload CSV/XLSX (max 10MB)
GET    /api/file/{file_id}            # Get file metadata
GET    /api/session/{session_id}/file # Get session's uploaded file
DELETE /api/file/{file_id}            # Delete uploaded file
POST   /api/query                     # Process chat query
GET    /api/history/{session_id}      # Retrieve chat history
DELETE /api/history/{session_id}      # Clear chat history
GET    /api/sessions                  # List all sessions
GET    /health                        # Health check
```

---

## 📄 License & Developer

**MIT License**

**Aditha Buwaneka** | [@AdithaBuwaneka](https://github.com/AdithaBuwaneka)  
Built for GenAI & Full Stack Engineering Technical Challenge

---

⭐ **Star this repository if you find it useful!**

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

**📚 Deployment Guides:**
- [Deploy to Hugging Face Spaces (Backend)](README_HUGGINGFACE.md)
- [MongoDB Atlas Setup Guide](MONGODB_SETUP.md)
- [Deployment Checklist](HF_DEPLOYMENT_CHECKLIST.md)

---

## 🎯 Features

- **Multi-Agent System:** Planner (Gemini 2.5 Flash) creates execution plans → Executor (PandasAI) generates Python code and results
- **Smart Classification:** Distinguishes greetings, chitchat, and data questions using semantic understanding
- **Auto-Visualization:** Generates charts (bar, line, pie, scatter) intelligently based on query intent
- **Context Memory:** Retains last 5 messages for seamless follow-up questions
- **Session Persistence:** Files and chats survive page refresh via MongoDB

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────┐
│         React Frontend (Vercel)                         │
│    FileUpload • ChatInterface • ChartDisplay            │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────────┐
│         FastAPI Backend (Hugging Face Spaces)           │
│    /upload • /query • /history • /sessions              │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────▼───────────┐
        │  Query Classifier      │
        │  (Gemini 2.5 Flash)    │
        └──┬──────────────────┬──┘
           │                  │
   [Greeting/Chitchat]   [Data Question]
           │                  │
    Simple Response    ┌──────▼─────────┐
                       │  LangGraph     │
                       │  Orchestrator  │
                       └─┬──────────┬───┘
                         │          │
                    ┌────▼────┐  ┌──▼────────┐
                    │ Planner │──│ Executor  │
                    │(Gemini) │  │(PandasAI) │
                    └─────────┘  └───────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼─────┐      ┌────────▼───────┐   ┌────────▼───────┐
   │ MongoDB  │      │  ImageKit CDN  │   │  Cache Memory  │
   │ (History)│      │  (Files/URLs)  │   │  (DataFrame)   │
   └──────────┘      └────────────────┘   └────────────────┘
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
- **MongoDB Atlas URI** (see [MONGODB_SETUP.md](MONGODB_SETUP.md))
- **Gemini API Key** (Google AI Studio)
- **ImageKit credentials** (public/private keys + URL endpoint)

### Backend Setup
```bash
cd backend
pip install -r requirements.txt

# Environment variables (create .env file or export)
export GEMINI_API_KEY="your-gemini-api-key"
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/dbname?retryWrites=true&w=majority"
export IMAGEKIT_PUBLIC_KEY="your-public-key"
export IMAGEKIT_PRIVATE_KEY="your-private-key"
export IMAGEKIT_URL_ENDPOINT="https://ik.imagekit.io/your-id"

# Run server (http://localhost:8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env

# Run dev server (http://localhost:5173)
npm run dev
```

---

## 📂 Project Structure

```
intelligent-data-room/
├── backend/app/
│   ├── agents/              # classifier.py, planner.py, executor.py
│   ├── graph/               # workflow.py (LangGraph orchestration)
│   ├── routers/             # upload.py, query.py (FastAPI endpoints)
│   ├── services/            # database.py, memory.py, imagekit_service.py
│   ├── models/schemas.py    # Pydantic models
│   └── main.py              # FastAPI app entry
├── frontend/src/
│   ├── components/          # FileUpload, ChatInterface, MessageList, ChartDisplay
│   ├── hooks/               # useChat.ts, useFileUpload.ts
│   ├── services/api.ts      # API client
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

**Smart Features:**
```
User: "Show top 10 customers by profit"
AI: [Returns result with chart]
User: "What about their locations?"
AI: [Understands context from previous query]

"Calculate Return Rate by Region. Don't give any chart"
→ Returns only table (respects preference)

"hi" or "how are you"
→ Responds conversationally without triggering data analysis
```

---

## 🔑 Key Technical Features

**1. Intelligent Classification**
- Semantic understanding using Gemini 2.5 Flash (no keyword matching)
- Handles ANY phrasing, typos, slang, multiple languages
- Context-aware: distinguishes greetings vs. follow-up questions

**2. Smart Visualization**
- Intent-based: Planner decides if charts add value
- Respects user preferences ("don't chart", "without graph")
- Handles contradictions intelligently

**3. Multi-Agent Workflow**
- Planner: Analyzes question + schema → Creates execution plan
- Executor: PandasAI generates Python → Executes → Returns results
- Fallback to Gemini API on PandasAI failures

**4. Context Management**
- MongoDB stores conversation history per session
- Last 5 messages used for follow-up detection
- Session persistence across page refreshes

---

## 📊 API Endpoints

```
POST   /api/upload              # Upload CSV/XLSX (max 10MB)
GET    /api/file/{file_id}      # Get file metadata
POST   /api/query               # Process chat query
GET    /api/history/{session}   # Retrieve chat history
DELETE /api/history/{session}   # Clear chat history
GET    /api/sessions            # List all sessions
GET    /health                  # Health check
```

---

## 📄 License & Developer

**MIT License**

**Aditha Buwaneka** | [@AdithaBuwaneka](https://github.com/AdithaBuwaneka)  
Built for GenAI & Full Stack Engineering Technical Challenge

---

⭐ **Star this repository if you find it useful!**

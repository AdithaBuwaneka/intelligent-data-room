# Intelligent Data Room

AI-powered data analysis platform with a multi-agent system. Upload CSV/XLSX files and chat with your data in natural language.

## 🌐 Live Demo

- **Frontend:** [intelligent-data-room.vercel.app](https://intelligent-data-room.vercel.app)
- **Backend API:** [huggingface.co/spaces/adithaf7/intelligent-data-room](https://huggingface.co/spaces/adithaf7/intelligent-data-room)

## 🎯 Features

- **Multi-Agent System** - Planner creates execution plans, Executor runs analysis
- **Natural Language Queries** - Ask questions about your data in plain English
- **Auto Visualizations** - Charts generated automatically for trends/comparisons
- **Context Retention** - Remembers conversation history for follow-up questions
- **Session Persistence** - Chat history saved across browser refreshes

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| AI/LLM | Google Gemini 2.5 Flash |
| Agent Framework | LangGraph |
| Data Analysis | PandasAI |
| Backend | FastAPI (Python) |
| Frontend | React + TypeScript + Vite |
| Database | MongoDB Atlas |
| File Storage | ImageKit |

## 📁 Project Structure

```
├── backend/          # FastAPI + LangGraph + PandasAI
├── frontend/         # React + TypeScript + Tailwind
└── README.md
```

## 🚀 Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env  # Set API URL
npm run dev
```

## 📝 Sample Queries

- "Show total sales by category"
- "Which region has highest profit?"
- "Create a pie chart of sales by region"
- "How has profit changed over the years?"

## 🏗️ Architecture

```
User Question → Planner Agent → Execution Plan → Executor Agent → Answer + Chart
                    ↓                                    ↓
              Google Gemini                        PandasAI + Gemini
```

## 📄 License

MIT License

---
title: Intelligent Data Room
emoji: 📊
colorFrom: blue
colorTo: indigo
sdk: docker
app_file: app/main.py
pinned: false
---

# Intelligent Data Room

[![Backend Status](https://img.shields.io/badge/Backend-Running-brightgreen)](https://adithaf7-intelligent-data-room.hf.space)
[![Frontend Status](https://img.shields.io/badge/Frontend-Live-blue)](https://intelligent-data-room.vercel.app)

AI-powered data analysis platform with a multi-agent system. Upload CSV/XLSX files and chat with your data in natural language.

## 🌐 Live Demo

| Component | URL |
|-----------|-----|
| **Frontend** | [intelligent-data-room.vercel.app](https://intelligent-data-room.vercel.app) |
| **Backend API** | [adithaf7-intelligent-data-room.hf.space](https://adithaf7-intelligent-data-room.hf.space) |
| **API Docs** | [adithaf7-intelligent-data-room.hf.space/docs](https://adithaf7-intelligent-data-room.hf.space/docs) |

## 🎯 Features

- **Multi-Agent System** - Planner creates execution plans, Executor runs analysis
- **Natural Language Queries** - Ask questions about your data in plain English
- **Auto Visualizations** - Charts generated automatically for trends/comparisons
- **Context Retention** - Remembers conversation history for follow-up questions

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| AI/LLM | Google Gemini 2.5 Flash |
| Agent Framework | LangGraph |
| Data Analysis | PandasAI |
| Backend | FastAPI (Python) |
| Frontend | React + TypeScript |
| Database | MongoDB Atlas |

##  Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📝 Sample Queries

- "Show total sales by category"
- "Create a pie chart of sales by region"
- "How has profit changed over the years?"

## 📄 License

MIT License

---
title: Intelligent Data Room API
emoji: 📊
colorFrom: blue
colorTo: purple
sdk: docker
sdk_version: "4.36.0"
python_version: "3.11"
app_port: 7860
pinned: false
license: mit
---

# Intelligent Data Room 🤖📊

A GenAI-powered data analysis platform using multi-agent system with Google Gemini.

## Features
- 📤 Upload CSV/XLSX files
- 💬 Chat with your data using natural language
- 📊 Automatic chart generation
- 🧠 Multi-agent system (Planner + Executor)
- 🔄 Context retention for follow-up questions

## Tech Stack
- **Backend:** FastAPI + PandasAI + LangGraph
- **AI:** Google Gemini 2.0 Flash
- **Storage:** ImageKit

## Usage
This is the backend API. Use with the frontend: [Deploy frontend to Vercel]

## Environment Variables Required
Set these in Space Settings → Repository secrets:
- `GEMINI_API_KEY`
- `IMAGEKIT_PRIVATE_KEY`
- `IMAGEKIT_PUBLIC_KEY`
- `IMAGEKIT_URL_ENDPOINT`

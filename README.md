# Intelligent Data Room

AI-powered data analysis platform using a Multi-Agent System (Planner + Executor) with LangGraph, PandasAI, and Google Gemini.

## Features

- **CSV/XLSX Upload** - Drag & drop files (max 10MB)
- **Natural Language Queries** - Ask questions about your data in plain English
- **Multi-Agent System** - Planner creates execution plans, Executor runs analysis
- **Auto Visualization** - Charts generated automatically (bar, line, pie, scatter)
- **Context Retention** - Remembers last 5 messages for follow-up questions
- **Session Management** - Persistent chat history per session

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS, Recharts |
| **Backend** | Python, FastAPI, LangChain, LangGraph, PandasAI |
| **AI** | Google Gemini 1.5 Flash |
| **Database** | MongoDB Atlas |
| **Storage** | ImageKit.io |
| **Deployment** | Vercel (frontend), Render (backend) |

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Frontend (React)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │ FileUpload  │  │    Chat     │  │  ChartDisplay   │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────┐
│                    Backend (FastAPI)                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │              LangGraph Workflow                   │   │
│  │  ┌─────────────┐         ┌─────────────────┐     │   │
│  │  │   Planner   │────────▶│    Executor     │     │   │
│  │  │   Agent     │         │     Agent       │     │   │
│  │  │  (Gemini)   │         │  (PandasAI)     │     │   │
│  │  └─────────────┘         └─────────────────┘     │   │
│  └──────────────────────────────────────────────────┘   │
└───────┬─────────────────┬─────────────────┬─────────────┘
        │                 │                 │
   ┌────▼────┐      ┌─────▼─────┐     ┌─────▼─────┐
   │ MongoDB │      │ ImageKit  │     │  Gemini   │
   │  Atlas  │      │    .io    │     │    API    │
   └─────────┘      └───────────┘     └───────────┘
```

## Quick Start

### Prerequisites

- Node.js 20.19+ or 22.12+
- Python 3.11+
- MongoDB Atlas account
- ImageKit.io account
- Google AI Studio API key

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/intelligent-data-room.git
cd intelligent-data-room
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run server
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with API URL

# Run dev server
npm run dev
```

### 4. Open Application

Visit: http://localhost:5173

## Environment Variables

### Backend (.env)

```env
# Google Gemini API
GEMINI_API_KEY=your_gemini_api_key

# MongoDB Atlas
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/dbname

# ImageKit.io
IMAGEKIT_PUBLIC_KEY=public_xxxxx
IMAGEKIT_PRIVATE_KEY=private_xxxxx
IMAGEKIT_URL_ENDPOINT=https://ik.imagekit.io/your_id

# Application
DEBUG=True
ALLOWED_ORIGINS=http://localhost:5173
```

### Frontend (.env)

```env
VITE_API_URL=http://localhost:8000
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/upload` | Upload CSV/XLSX file |
| GET | `/api/file/{id}` | Get file metadata |
| POST | `/api/query` | Send chat query |
| GET | `/api/history/{session}` | Get chat history |

## Sample Prompts

Test with the Sample Superstore dataset:

### Easy
1. Create a bar chart showing total Sales and Profit by Category
2. Show sales distribution by Region using a pie chart
3. Which Customer Segment places the most orders?
4. Top 5 States by total Sales
5. How has Profit changed over the years?

### Medium
6. Which Sub-Categories are unprofitable?
7. Compare Sales Trend of different Ship Modes
8. Top 10 Customers by Profit
9. Is there a correlation between Discount and Profit?
10. Calculate Return Rate by Region

## Deployment

### Render (Backend)

1. Create new Web Service
2. Connect GitHub repository
3. Settings:
   - **Runtime:** Python 3.11
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables
5. Deploy

### Vercel (Frontend)

1. Import GitHub repository
2. Settings:
   - **Framework:** Vite
   - **Build:** `npm run build`
   - **Output:** `dist`
3. Add `VITE_API_URL` environment variable
4. Deploy

## Project Structure

```
intelligent-data-room/
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # API services
│   │   ├── types/          # TypeScript types
│   │   └── App.tsx         # Main component
│   └── package.json
├── backend/
│   ├── app/
│   │   ├── agents/         # Planner & Executor
│   │   ├── graph/          # LangGraph workflow
│   │   ├── models/         # Pydantic schemas
│   │   ├── routers/        # API endpoints
│   │   ├── services/       # DB, ImageKit, Memory
│   │   └── main.py         # FastAPI app
│   └── requirements.txt
└── README.md
```

## License

MIT License

---

Built for GenAI & Full Stack Engineering Challenge

# Frontend - Intelligent Data Room

React + TypeScript frontend for the AI-powered data analysis platform.

## 🌐 Live Demo

[intelligent-data-room.vercel.app](https://intelligent-data-room.vercel.app)

## ✨ Features

- Drag-and-drop file upload (CSV/XLSX)
- Real-time chat interface
- Interactive charts (Recharts)
- Session history & switching
- Mobile responsive design

## 🚀 Quick Start

```bash
npm install
cp .env.example .env
npm run dev
```

## 🔧 Environment Variables

```env
VITE_API_URL=http://localhost:8000
```

For production (Vercel):
```env
VITE_API_URL=https://adithaf7-intelligent-data-room.hf.space
```

## 📁 Structure

```
src/
├── components/     # UI components
│   ├── ChatInterface.tsx
│   ├── FileUpload.tsx
│   ├── MessageList.tsx
│   └── ChartDisplay.tsx
├── hooks/          # Custom React hooks
│   ├── useChat.ts
│   └── useFileUpload.ts
├── types/          # TypeScript types
└── App.tsx         # Main app
```

## 🛠️ Tech Stack

- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS
- Recharts (visualizations)

## 📦 Build

```bash
npm run build     # Production build
npm run preview   # Preview build
```

## 🚀 Deploy to Vercel

```bash
vercel
```

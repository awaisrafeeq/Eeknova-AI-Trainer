# Eeknova AI Trainer

This repository contains:

- `yoga_project/`: FastAPI backend (Yoga, Dashboard stats, Chess/Zumba progress APIs)
- `frontend/`: Next.js frontend

## Prerequisites

- Python 3.10+
- Node.js 18+

## Backend (FastAPI) - Run Locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r yoga_project/requirements.txt
```

3. Start the API server:

```bash
python main.py
```

Backend will be available at:

- `http://localhost:8000`

## Frontend (Next.js) - Run Locally

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Create `frontend/.env.local` and set the backend URLs:

```env
OPENAI_API_KEY=your-api-key
```

3. Start the dev server:

```bash
npm run dev
```

Frontend will be available at:

- `http://localhost:3000`

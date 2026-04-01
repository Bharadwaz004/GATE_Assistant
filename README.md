# 🎓 GATE Study Planner — AI-Powered Preparation Platform

A production-grade SaaS application that generates personalized study plans for GATE aspirants using Hugging Face LLMs, tracks progress with streaks, and matches users with compatible study partners.

## Tech Stack

| Layer       | Technology                                      |
|-------------|--------------------------------------------------|
| Frontend    | React 18 + Vite, Tailwind CSS, Zustand           |
| Backend     | FastAPI, Pydantic v2, SQLAlchemy 2.0              |
| Database    | PostgreSQL 15, Redis 7                            |
| AI/ML       | HuggingFace Transformers, Sentence-Transformers   |
| Task Queue  | Celery + Redis                                    |

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

### Docker (Optional)
```bash
docker-compose up --build
```

## Architecture

```
gate-study-planner/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry
│   │   ├── api/routes/           # REST API endpoints
│   │   ├── services/             # Business logic layer
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic validation schemas
│   │   ├── db/                   # Database configuration
│   │   ├── ai/                   # HuggingFace AI module
│   │   └── utils/                # Helpers and utilities
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/           # Reusable UI components
│   │   ├── pages/                # Route-level page components
│   │   ├── store/                # Zustand state management
│   │   ├── hooks/                # Custom React hooks
│   │   └── utils/                # Frontend utilities
│   └── package.json
└── docker-compose.yml
```

## API Endpoints

| Method | Path              | Description                  |
|--------|-------------------|------------------------------|
| POST   | /api/auth/signup  | Register new user            |
| POST   | /api/auth/login   | Authenticate user            |
| POST   | /api/onboarding   | Submit onboarding profile    |
| GET    | /api/profile      | Get user profile             |
| POST   | /api/plan/generate| Generate AI study plan       |
| GET    | /api/plan/daily   | Get today's study tasks      |
| POST   | /api/plan/task    | Update task status           |
| GET    | /api/streak       | Get streak information       |
| GET    | /api/match        | Get study partner matches    |

## Environment Variables

See `.env.example` files in both `backend/` and `frontend/` directories.

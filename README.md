# King Mave Digital Automation Hub

A production-ready starter for the King Mave Digital business: WhatsApp CRM automation, lead management, and a social media scheduler for content publishing.

## Features

- WhatsApp lead capture and automatic welcome messaging
- Persistent CRM for leads and conversations
- Social media content scheduler with publishing status
- Lead analytics summary endpoint
- Admin dashboard for overview and manual actions
- SQLite database support with easy upgrade path to Postgres
- Docker-ready deployment

## Tech stack

- FastAPI
- SQLAlchemy
- SQLite
- Pydantic v2
- Uvicorn
- Docker

## Quick start

1. Create a Python virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy environment example:

```bash
cp .env.example .env
```

4. Run the app:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Open the dashboard:

- http://localhost:8000/

## Core endpoints

- `GET /health`
- `GET /api/leads`
- `POST /api/leads`
- `POST /api/whatsapp/webhook`
- `POST /api/whatsapp/send`
- `GET /api/scheduler/posts`
- `POST /api/scheduler/posts`
- `POST /api/scheduler/posts/{id}/publish`
- `GET /api/analytics/summary`

## Example lead payload

```json
{
  "name": "Aisha",
  "phone": "+2348012345678",
  "email": "aisha@example.com",
  "source": "website",
  "interest": "AI automation",
  "notes": "Looking for WhatsApp funnel automation"
}
```

## Example scheduled post payload

```json
{
  "platform": "instagram",
  "caption": "We help businesses grow with AI + WhatsApp + content systems.",
  "status": "scheduled",
  "scheduled_for": "2026-10-04T12:00:00"
}
```

## Environment variables

See `.env.example` for all supported options.

## Deployment

This project includes a Dockerfile for container deployment.

```bash
docker build -t kmd-automation-hub .
docker run -p 8000:8000 kmd-automation-hub
```

## Production notes

- Replace the demo WhatsApp values with real credentials.
- Consider upgrading from SQLite to PostgreSQL for production data integrity.
- Add your own authentication layer for the admin dashboard.
- Connect the scheduler to actual social APIs when ready.

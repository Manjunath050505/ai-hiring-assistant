# AI Hiring Assistant

Production-quality MVP for an HR platform using Hunar.ai Voice AI Agents. The candidate uses a public link to submit their name/phone/consent; the FastAPI backend starts a Hunar outbound call; Hunar conducts the interview and sends webhooks; the HR dashboard displays status and structured evaluation.

## Architecture
- Next.js + TypeScript + Tailwind frontend
- FastAPI + Pydantic + httpx backend
- PostgreSQL via SQLAlchemy/Alembic
- Hunar external Voice AI API server-side only

## Local development
### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000.

For a zero-credential demo, set `HUNAR_MOCK_MODE=true` and use the seeded/sample workflow. Real Hunar credentials belong only in the backend environment.

## Environment variables
See `backend/.env.example` and `frontend/.env.example`.

## Hunar webhooks
Configure Hunar to call `POST https://<backend-domain>/api/webhooks/hunar`. Set the webhook signing secret in `HUNAR_WEBHOOK_SECRETS`. The implementation verifies `X-Hunar-Signature` against `timestamp + "." + raw request body` and rejects stale requests.

## Deployment
Frontend is Vercel-compatible. Backend is Render-compatible. PostgreSQL can be Supabase. Set production CORS and environment variables in the platform dashboards.

## Security
No Hunar secret is used in browser code. Public candidate tokens are random URL-safe values. Webhook events are idempotently recorded.

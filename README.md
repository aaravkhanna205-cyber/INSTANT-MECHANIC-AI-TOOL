# Instant Mechanic AI Diagnosis — Deployable Starter Prototype

**Status:** Working starter prototype with React frontend and FastAPI backend. It is NOT a trained AI model or a verified automotive diagnostic system. It uses keyword-based candidate matching against a configurable fault database. It is intended for demonstration and incremental development.

## Run locally

Install Python 3.11+ and Node.js 20+.

Terminal 1:
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
Terminal 2:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173. Backend docs: http://localhost:8000/docs.

## Deploy backend to Render
1. Push this entire folder to a private GitHub repository (do not commit secrets).
2. Render > New > Web Service > Connect repository.
3. Root directory: `backend`. Environment: Docker. Dockerfile path: `./Dockerfile` relative to root directory.
4. Set `CORS_ORIGINS` to your actual frontend origin (e.g. https://your-app.vercel.app), without trailing slash.
5. Deploy and verify `https://YOUR-BACKEND.onrender.com/api/health`.
6. The prototype SQLite DB is ephemeral on many free hosts; seed data may reset. Use a persistent disk or migrate to managed PostgreSQL before relying on saved changes.

## Deploy frontend to Vercel
1. Import the same GitHub repository in Vercel.
2. Set Root Directory to `frontend`, Framework Preset: Vite, Build Command: `npm run build`, Output Directory: `dist`.
3. Set environment variable `VITE_API_URL=https://YOUR-BACKEND.onrender.com` (no trailing slash).
4. Deploy, then update backend `CORS_ORIGINS` to the real frontend URL and redeploy backend.
5. Test from a phone browser. To make a home-screen shortcut, use browser menu > Add to Home screen (where supported).

## Expand fault categories
Use `backend/main.py` SEED to add example entries during development, or import JSON with the admin endpoint **only in a trusted, authenticated deployment**. The included import endpoint is intentionally disabled by default because it has no authentication. Do not expose it publicly enabled. Each record has:
`category,subcategory,symptoms,questions,checks,action,urgency,parts,price_min,price_max,labour_min,labour_max,repair_minutes`.
Questions are separated by `|`. The price fields in sample records are zero to signify that NO verified vehicle-specific price has been loaded, not that repairs are free.

## Production work still required
- Add authentication, roles and protected admin CRUD before enabling public data editing.
- Replace SQLite with PostgreSQL; use migrations, backups and audit logs.
- Add vehicle fitment database, region-specific validated pricing, supplier timestamps, labor bands, and supporting references.
- Add multilingual support, accessibility, rate limiting, privacy policy, monitoring, abuse prevention and diagnostic safety rules.
- Replace keyword matching with a tested retrieval + LLM question generator, with deterministic guardrails and human mechanic escalation.
- Add tests, fault evaluation set, red-flag handling, and expert-reviewed repair procedures.
- Add an optional Android PWA manifest/service worker or native wrapper after testing.

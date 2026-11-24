# Supply Mart

A small grocery marketplace with JWT authentication, role based access control, shop groups with member permissions and an admin dashboard. React + TypeScript frontend, FastAPI backend, Supabase PostgreSQL, deployed on Vercel.

- Live: https://2310364-s6-supply-mart.vercel.app
- API docs: https://2310364-s6-supply-mart.vercel.app/api/docs

```
backend/    FastAPI app (routes under /api/v1)
frontend/   Vite + React + TypeScript
docs/       PRD, SRS, TDD, final report, viva notes
vercel.json /api/* goes to backend, everything else to frontend
```

## Features

- JWT login: 15-minute access token and a rotating httpOnly refresh cookie, logout, session list and revoke, login lockout
- Roles `user` and `admin`, ownership rules, one reusable RBAC module
- Shop groups with member permissions (`create`, `update`, `stock`); only the owner can rename, delete or manage members
- Admin dashboard: statistics, users (search, filters, ban, role change, bulk actions), content moderation, activity log, security view, CSV export

## Test accounts

Passwords are in the submission form and the PDF report, not in this repository.

| User ID (email) | Role | Notes |
|---|---|---|
| admin1@supplymart.test | admin | |
| admin2@supplymart.test | admin | |
| rahim@supplymart.test | user | owner of group "Mirpur Fresh Mart" |
| karim@supplymart.test | user | member of the group with `create`, `update` |
| salma@supplymart.test | user | member of the group with `stock` only |

Shared group: **Mirpur Fresh Mart**, owner rahim. Karim may add and edit products, salma may only change stock, and neither can rename or delete the group or manage members.

## Requirements

- [Python](https://www.python.org/downloads/) 3.10+
- [Node.js](https://nodejs.org/) 22+

## Run locally

**Backend** (terminal 1):

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
fastapi dev main.py             # http://localhost:8000/api/docs
```

Locally no variables are needed: SQLite and development keys are used. To create the demo accounts (the password is read from the environment):

```bash
DEMO_PASSWORD="<choose-one>" python -m app.seed_demo     # PowerShell: $env:DEMO_PASSWORD="<choose-one>"; python -m app.seed_demo
```

Run the tests with `pytest -q` (21 tests).

**Frontend** (terminal 2):

```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

## Environment variables

See `backend/.env.example`. Set these on Vercel:

| Name | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (Supabase) |
| `JWT_SECRET` | signs access tokens |
| `PEPPER` | secret mixed into password hashes |
| `CORS_ORIGINS` | allowed frontend origin |

## Deploy

Push to `main`; Vercel redeploys automatically. Keep **Root Directory** as `./`.
# ODMS — Organ Donation Matching System

A full-stack academic prototype for the Software Engineering project. It includes donor management, recipient waitlist management, a transparent demonstration matching engine, login/role checks, notifications, an audit trail, and a dashboard backed by a relational database.

> **Clinical disclaimer:** This application uses synthetic demonstration records and simplified screening rules. It is not clinically validated, does not implement official organ allocation policy, and must not be used for real patients or transplant decisions. All potential candidates require qualified clinical review.

## Stack
- Frontend: React + Vite + JavaScript
- Backend: Flask REST API + SQLAlchemy + Flask-Migrate-ready schema
- Database: SQLite by default for quick local setup; PostgreSQL supported through `DATABASE_URL`
- Authentication: server-side Flask session and bcrypt password hashes

## Features
- Login/logout with backend session checks and account lock after repeated failed login attempts
- Donor create/list/search/filter/detail/edit/status management
- Recipient create/list/search/filter/edit and active/inactive/matched waitlist states
- Matching runs saved to the database, filtering active recipients by organ type and simplified ABO rules, with explainable demo urgency/waiting-time ranking
- Match history and result review; accepted demo results lock donor availability to prevent reuse
- In-app notifications and restricted read-only audit trail
- Dashboard counts fetched from database queries
- Synthetic demo data loaded only when the database is empty

## Demo credentials
- System Administrator: `admin@odms.local` / `Demo@12345`
- Medical Coordinator: `coordinator@odms.local` / `Demo@12345`

These credentials are for local demonstration only. Change them before any deployment. The audit page is visible to admin roles; the matching workflow is available to both demo roles.

## Quick start (Windows PowerShell)
Open two terminals in the `odms` folder.

### 1. Backend
```powershell
cd backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python app.py
```
The API starts at `http://127.0.0.1:5000`. The SQLite database `odms.db` is created automatically in the backend folder. On first start, synthetic sample data is seeded.

### 2. Frontend
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```
Open `http://127.0.0.1:5173`.

### macOS/Linux
Backend:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```
Frontend:
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## PostgreSQL setup
1. Create a PostgreSQL database named `odms` and a dedicated local user.
2. In `backend/.env`, set a connection string, for example:
   `DATABASE_URL=postgresql+psycopg://odms_user:YOUR_PASSWORD@localhost:5432/odms`
3. Set a strong random `SECRET_KEY`.
4. Run `python app.py` to initialize tables. For production-quality schema evolution, use the migrations workflow described below.

Do not commit `.env` files. PostgreSQL is preferred for the SRS; SQLite is only the zero-setup local fallback.

## Migrations
Install dependencies, then from `backend` run:
```bash
flask --app app db init
flask --app app db migrate -m "initial schema"
flask --app app db upgrade
```
The project includes Flask-Migrate in dependencies. The current quick-start also creates missing tables automatically for the local prototype. Do not delete an existing database to apply schema changes.

## Tests
From `backend` with the virtual environment active:
```bash
pytest -q
```
Tests use an isolated in-memory SQLite database and cover authentication, unauthorized access, donor/recipient creation, duplicate IDs, and a matching run.

## API overview
- `GET /api/health`
- `POST /api/auth/login`, `POST /api/auth/logout`, `GET /api/auth/me`
- `GET/POST /api/donors`, `GET/PATCH /api/donors/<id>`, `PATCH /api/donors/<id>/status`
- `GET/POST /api/recipients`, `GET/PATCH /api/recipients/<id>`, `PATCH /api/recipients/<id>/status`
- `POST /api/matches/run`, `GET /api/matches/runs`, `GET /api/matches/runs/<id>`, `GET /api/matches/results`, `PATCH /api/matches/results/<id>/review`
- `GET /api/notifications`, `PATCH /api/notifications/<id>/read`
- `GET /api/audit-logs` (admin/auditor roles)
- `GET /api/dashboard/summary`

## Database model overview
`Facility` relates to `User`, `Donor`, and `Recipient`. `MatchRun` stores each run and references its donor and initiating user. `MatchResult` connects a run, donor, and recipient and stores the ranking explanation and review state. `Notification` belongs to a user. `AuditLog` stores action metadata without sensitive clinical notes.

## Demo walkthrough (2–5 minutes)
1. Sign in as the System Administrator.
2. Show the dashboard counts from the database.
3. Open Donor Registry and inspect synthetic donor records; add a new synthetic donor.
4. Open Recipient Waitlist and add a recipient with the same organ type.
5. Open Matching Engine, select an available donor, and run matching.
6. Show ranked potential candidates and the explanation; point out that inactive recipients are excluded.
7. Review a result and save a demo status.
8. Open Match History, Notifications, and Audit Trail to show persisted workflow events.
9. End by stating that the algorithm is educational and not clinically validated.

**Demo video link:** [Paste your actual 2–5 minute video URL here after uploading it.]

## Known limitations / future scope
- Simplified ABO screening and demo scoring only; no validated clinical allocation rules or HLA crossmatch.
- No real hospital EHR, national registry, SMS, pager, or email integration.
- This is a local academic prototype. Before real deployment, add full clinical governance, production security review, robust facility-level authorization, operational monitoring, and validated allocation logic.
- The initial schema is prototype-oriented; review/extend migrations before evolving the schema on an existing database.

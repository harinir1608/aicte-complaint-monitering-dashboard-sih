# AICTE Integrated Institution Complaint Monitoring Dashboard

<p align="center">
  <img src="frontend/public/logo.png" alt="AICTE Logo" width="80"/>
</p>

<p align="center">
  <strong>अखिल भारतीय तकनीकी शिक्षा परिषद्</strong><br/>
  All India Council for Technical Education
</p>

<p align="center">
  Smart India Hackathon 2024 · Problem Statement 26264
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12-blue" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.115-green" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/React-18-61DAFB" alt="React"/>
  <img src="https://img.shields.io/badge/SQLAlchemy-2.x-red" alt="SQLAlchemy"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow" alt="License"/>
</p>

---

> ⚠️ **DEMO DATA** — All institutions, complaints, and cases in the seeded database are fictional. This is not actual AICTE data.

---

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Architecture](#architecture)
4. [Quick Start](#quick-start)
5. [Local Development](#local-development)
6. [One-Click Launch](#one-click-launch)
7. [Demo Accounts](#demo-accounts)
8. [API Reference](#api-reference)
9. [How AI Overlap Detection Works](#how-ai-overlap-detection-works)
10. [Institution Digital Twin](#institution-digital-twin)
11. [Cross-Bureau Conflict Prevention](#cross-bureau-conflict-prevention)
12. [Running Tests](#running-tests)
13. [Configuration Reference](#configuration-reference)
14. [Production Deployment](#production-deployment)
15. [Known Limitations](#known-limitations)

---

## Overview

The **AICTE Integrated Institution Complaint Monitoring Dashboard** centralises institution-related complaints and regulatory cases across AICTE's Regulation Bureau (RB), Public Grievance Redressal Cell (PGRC), regional offices, and authorised Bureaus/Cells.

### Problem Statement 26264

Fragmented case management across departments leads to:
- Duplicate effort on overlapping cases
- Missed deadlines due to lack of a unified view
- Coordination gaps between bureaus handling the same institution
- No single source of truth for institutional compliance history

This platform solves all of the above.

---

## Key Features

### Core Platform
| Feature | Description |
|---------|-------------|
| **Unified Complaint Intake** | Portal, email, letter, RTI, court orders, walk-in |
| **Case Lifecycle Management** | Received → Pending → Under Process → Disposed/Closed |
| **SLA Monitoring** | Configurable deadlines with escalation reminders |
| **Role-Based Access Control** | 6 roles — Admin, RB Officer, PGRC Officer, Bureau Officer, Regional Officer, Senior Management |
| **Document Management** | Upload/download supporting documents per case |
| **Audit Trail** | Immutable chronological history for every case action |
| **In-App Notifications** | Assignment, deadline, overlap, and escalation alerts |

### AI / Intelligence Features
| Feature | Description |
|---------|-------------|
| **Explainable AI Overlap Detection** | 3-stage pipeline: Exact ID → Fuzzy Name → Semantic Similarity |
| **Institution Digital Twin** | Unified 360° institutional profile with relationship graph |
| **Cross-Bureau Conflict Prevention** | Rule-based detection of parallel actions and competing deadlines |
| **Smart Dashboard** | 12 live KPI cards, 5 charts, all backed by real database queries |

### Institution Directory
| Feature | Description |
|---------|-------------|
| **4,634 Real Institutions** | Imported from official AICTE PDF with Permanent IDs |
| **State/District/City Data** | 97% coverage from Institute_List PDF |
| **Search & Filter** | By name, permanent ID, state, type, status |

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (port 5173)                   │
│  React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui  │
│  React Router · TanStack Query · Recharts · React Flow    │
└────────────────────────┬────────────────────────────────┘
                         │ REST + JSON (JWT Bearer)
┌────────────────────────▼────────────────────────────────┐
│                    BACKEND (port 8000)                    │
│     Python 3.12 · FastAPI · SQLAlchemy 2.x · Alembic      │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Matching    │  │  Conflict    │  │  Scheduler    │  │
│  │  Engine      │  │  Engine      │  │  APScheduler  │  │
│  │  RapidFuzz   │  │  Rule-based  │  │  SLA checks   │  │
│  │  SentTransf. │  │              │  │               │  │
│  └──────────────┘  └──────────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ SQLAlchemy ORM
┌────────────────────────▼────────────────────────────────┐
│              DATABASE — SQLite (dev) / PostgreSQL (prod)  │
│  17 tables: users, institutions, complaints, cases,       │
│  overlap_alerts, conflict_alerts, audit_logs, ...         │
└─────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Docker (Recommended)
```bash
git clone <repo-url>
cd aicte-complaint-dashboard
cp .env.example .env
# Edit .env — set a strong SECRET_KEY

docker compose up -d
docker compose exec backend python -m app.db.seed

# Open http://localhost:5173
```

### Windows — One Click
Double-click **`run.bat`** in the project root. It will:
1. Kill any old processes on ports 8000 and 5173
2. Start the FastAPI backend (minimised window)
3. Start the Vite frontend (minimised window)
4. Open http://localhost:5173 in your browser

---

## Local Development

### Backend Setup (conda — recommended)

```bash
# Create and activate conda environment
conda create -n ps2 python=3.12 -y
conda activate ps2

# Install dependencies
cd backend
pip install -r requirements.txt
pip install "pydantic[email]"

# Copy environment file
cp ../.env.example ../.env
# Edit .env → set DATABASE_URL, SECRET_KEY

# Run migrations
python -m alembic upgrade head

# Seed demo data
python -m app.db.seed

# Start server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# Available at http://localhost:5173
```

### Enable Semantic AI Matching (Optional)
```env
# In .env
ENABLE_SEMANTIC_MATCHING=true
SEMANTIC_MODEL_NAME=all-MiniLM-L6-v2   # ~90MB download on first use
```

---

## One-Click Launch

**`run.bat`** — Windows batch script at the project root.

```
Double-click run.bat
  └─ Kills old processes on 8000 and 5173
  └─ Starts Backend  → http://localhost:8000
  └─ Starts Frontend → http://localhost:5173
  └─ Opens browser automatically
```

To stop: close the two minimised command windows (`AICTE Backend` and `AICTE Frontend`).

---

## Demo Accounts

All demo passwords: **`Demo@1234`**

| Email | Role | Access Level |
|-------|------|-------------|
| `admin@aicte.gov.in` | System Administrator | Full access — all bureaus, all data |
| `rb.officer@aicte.gov.in` | RB Officer | Regulation Bureau cases |
| `pgrc.officer@aicte.gov.in` | PGRC Officer | PGRC Cell cases |
| `pgrc.officer2@aicte.gov.in` | PGRC Officer | PGRC Cell cases |
| `ab.officer@aicte.gov.in` | Bureau Officer | Approval Bureau cases |
| `north.regional@aicte.gov.in` | Regional Officer | Northern Region |
| `south.regional@aicte.gov.in` | Regional Officer | Southern Region |
| `management@aicte.gov.in` | Senior Management | Read-only across all |

---

## API Reference

Interactive docs: **http://localhost:8000/api/docs** (Swagger UI)

### Authentication
```
POST   /api/v1/auth/login              Authenticate → JWT tokens
GET    /api/v1/auth/me                 Current user profile
POST   /api/v1/auth/refresh            Refresh access token
POST   /api/v1/auth/change-password    Change password
```

### Institutions
```
GET    /api/v1/institutions                     List with search/filter
POST   /api/v1/institutions                     Create institution
GET    /api/v1/institutions/{id}                Get institution
PATCH  /api/v1/institutions/{id}                Update institution
GET    /api/v1/institutions/{id}/profile        Digital Twin profile
GET    /api/v1/institutions/{id}/graph          Relationship graph (React Flow)
GET    /api/v1/institutions/{id}/cases          All cases for institution
GET    /api/v1/institutions/search              Autocomplete search
```

### Complaints & Cases
```
GET    /api/v1/complaints                       List complaints
POST   /api/v1/complaints                       Register new complaint
GET    /api/v1/complaints/{id}                  Complaint detail
POST   /api/v1/complaints/{id}/create-case      Create case from complaint
GET    /api/v1/cases                            List cases
PATCH  /api/v1/cases/{id}/status                Update case status
POST   /api/v1/cases/{id}/assign                Assign to officer
POST   /api/v1/cases/{id}/transfer              Transfer to bureau
POST   /api/v1/cases/{id}/actions               Add remark/action
GET    /api/v1/cases/{id}/history               Full action history
POST   /api/v1/cases/{id}/related-cases         Link related case
```

### AI Overlap Detection
```
GET    /api/v1/overlaps                         List overlap alerts
GET    /api/v1/overlaps/{id}                    Alert detail with explanation
POST   /api/v1/overlaps/{id}/review             Submit review decision
GET    /api/v1/overlaps/{id}/history            Review history
POST   /api/v1/overlaps/run-check/{case_id}     Manually trigger overlap scan
```

### Conflict Prevention
```
GET    /api/v1/conflicts                        List conflict warnings
GET    /api/v1/conflicts/{id}                   Conflict detail
POST   /api/v1/conflicts/scan                   Run conflict detection
POST   /api/v1/conflicts/{id}/review            Acknowledge/resolve warning
```

### Dashboard & Reports
```
GET    /api/v1/dashboard/summary                12 KPI counts (live DB)
GET    /api/v1/dashboard/trends                 Monthly intake/disposal
GET    /api/v1/dashboard/workload               Bureau workload breakdown
GET    /api/v1/dashboard/institution-table      Institution stats table
GET    /api/v1/dashboard/ageing                 Case ageing buckets
GET    /api/v1/reports/institutions             Institution report (JSON/CSV)
GET    /api/v1/reports/ageing                   Ageing report
GET    /api/v1/reports/workload                 Workload report
GET    /api/v1/reports/overlaps                 Overlap outcomes report
```

---

## How AI Overlap Detection Works

The system uses a **3-stage explainable pipeline** — every alert includes human-readable reasons, never a black-box score.

### Stage 1 — Candidate Discovery
Queries active cases sharing an institution with the incoming case:
```
Priority 1 → Exact institution_id (same DB record)
Priority 2 → Matching AICTE Permanent ID (e.g. "1-1234567")
Priority 3 → RapidFuzz fuzzy name match ≥ 80% threshold
```

### Stage 2 — Three Independent Signals

| Signal | Tool | Measures |
|--------|------|---------|
| **Institution Score** | RapidFuzz `token_sort_ratio` + `partial_ratio` | Name similarity (0–100%) |
| **Lexical Text Score** | RapidFuzz `token_set_ratio` | Word overlap in subject+description (0–100%) |
| **Semantic Score** | Sentence Transformers `all-MiniLM-L6-v2` | Meaning similarity via cosine distance (0–100%) |

**Combined formula:**
```
combined = 0.60 × institution_score + 0.40 × text_score
(if semantic ON: text contribution = 0.40×lexical + 0.60×semantic)
```

### Stage 3 — Explainability
Every alert stores plain-English reasons:
```
"Exact institution match: both cases share the same AICTE Permanent ID."
"Institution name fuzzy match: similarity 88.5% (threshold 80.0%)."
"Complaint text similarity: 76.2% lexical overlap (threshold 70.0%)."
"Semantic similarity: 83.1% via sentence embeddings."
```

### Configurable Thresholds (`.env`)
```env
INSTITUTION_NAME_THRESHOLD=80.0
COMPLAINT_SIMILARITY_THRESHOLD=70.0
ENABLE_SEMANTIC_MATCHING=false
SEMANTIC_MODEL_NAME=all-MiniLM-L6-v2
```

---

## Institution Digital Twin

Each institution has a **360° profile** at `/institutions/{id}`:

- **Identity** — Name, AICTE Permanent ID, address, state, district, city
- **Case Statistics** — Total, active, overdue, pending, disposed counts
- **Overlap Alerts** — Unresolved alerts involving this institution
- **Case History** — Chronological all-bureau case timeline
- **Relationship Graph** — Interactive React Flow diagram showing links between cases, complaints, and bureaus

The graph data is served from `/api/v1/institutions/{id}/graph` and shows:
- Institution node (central)
- Case nodes (coloured by status)
- Bureau nodes
- Edges representing assignments and overlaps

---

## Cross-Bureau Conflict Prevention

A separate rule-based engine (distinct from overlap detection) identifies **coordination issues** between bureaus:

| Rule | Triggers When |
|------|--------------|
| `multi_bureau_same_issue` | Multiple bureaus have active cases on the same institution and similar complaint category |
| `competing_deadlines` | Related cases have deadlines within 7 days of each other |
| `parallel_escalation` | One case is escalated while a related case in another bureau is still under process |
| `transfer_conflict` | A case was transferred while a related case remains active elsewhere |

Each warning includes:
- Institution and affected case IDs
- Rule triggered + plain-English explanation
- Severity (high / medium / low)
- Recommended next step
- Review and resolution status

---

## Running Tests

```bash
cd backend
conda activate ps2

# All tests with coverage
pytest tests/ -v --cov=app --cov-report=term-missing

# Individual test files
pytest tests/test_auth.py -v
pytest tests/test_overlap.py -v
pytest tests/test_conflicts.py -v
```

| Test File | Covers |
|-----------|--------|
| `test_auth.py` | Login, /me, change password, 401/403 flows |
| `test_institutions.py` | CRUD, search, duplicate ID prevention |
| `test_complaints.py` | Complaint registration, numbering, bureau filtering |
| `test_cases.py` | Lifecycle, assignments, transfers, status transitions |
| `test_overlap.py` | Exact/fuzzy/semantic matching, alert creation, deduplication, review |
| `test_dashboard.py` | Live KPI counts, trends, overdue detection |
| `test_notifications.py` | Assignment notifications, mark read, deadline reminders |
| `test_search_pagination.py` | Pagination, filter accuracy |
| `test_reports.py` | CSV export, date filters |

---

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./aicte_dev.db` | DB connection — use PostgreSQL in production |
| `SECRET_KEY` | *(dev placeholder)* | JWT signing key — **must change in production** |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Access token lifetime (8 h) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `BACKEND_CORS_ORIGINS` | `["http://localhost:5173"]` | Allowed CORS origins |
| `USE_LOCAL_STORAGE` | `true` | Local file uploads (dev) |
| `LOCAL_STORAGE_PATH` | `./local_storage` | Upload directory |
| `AZURE_STORAGE_CONNECTION_STRING` | *(empty)* | Azure Blob Storage |
| `AZURE_STORAGE_CONTAINER_NAME` | `aicte-documents` | Azure container |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `ENABLE_SEMANTIC_MATCHING` | `false` | Enable sentence-transformers AI |
| `SEMANTIC_MODEL_NAME` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `INSTITUTION_NAME_THRESHOLD` | `80.0` | Fuzzy name match threshold (%) |
| `COMPLAINT_SIMILARITY_THRESHOLD` | `70.0` | Text similarity threshold (%) |
| `SMTP_HOST` | *(empty)* | Email server |
| `SMTP_PORT` | `587` | Email port |
| `SMTP_USER` | *(empty)* | Email username |
| `SMTP_PASSWORD` | *(empty)* | Email password |
| `FRONTEND_URL` | `http://localhost:5173` | Used in email notification links |

---

## Production Deployment

### Azure App Service

```bash
# 1. Provision Azure resources
#    - Azure Database for PostgreSQL Flexible Server
#    - Azure App Service (Python 3.12, B2 SKU minimum)
#    - Azure Blob Storage account
#    - Azure Key Vault for secrets

# 2. Set App Service environment variables
DATABASE_URL=postgresql://...@...postgres.database.azure.com/aicte_db?sslmode=require
SECRET_KEY=<64-char random string>
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
ENVIRONMENT=production
USE_LOCAL_STORAGE=false
ENABLE_SEMANTIC_MATCHING=false

# 3. Deploy backend
az webapp up --name aicte-dashboard-api --runtime PYTHON:3.12

# 4. Run migrations
az webapp ssh
python -m alembic upgrade head
python -m app.db.seed   # demo only — remove before go-live

# 5. Build and deploy frontend (static hosting or App Service)
cd frontend && npm run build
# Deploy dist/ to Azure Static Web Apps or serve via nginx
```

### HTTPS
Terminate TLS at the Azure Application Gateway or App Service level. Never expose the FastAPI server directly on port 443.

### Secret Management
Store all secrets in **Azure Key Vault** and reference them as App Service Key Vault references. Rotate `SECRET_KEY` periodically (this invalidates all active sessions).

### Backups
Enable automated backups in Azure Database for PostgreSQL (daily snapshots, 7-day retention minimum). Test restore procedures quarterly.

---

## Known Limitations

1. **Semantic matching disabled by default** — The `all-MiniLM-L6-v2` model (~90 MB) is not downloaded automatically. Set `ENABLE_SEMANTIC_MATCHING=true` and pre-download the model before deploying to air-gapped environments.

2. **SQLite in development** — The default `.env` uses SQLite for zero-config setup. Switch to PostgreSQL for production by setting `DATABASE_URL`.

3. **Email notifications require SMTP** — Leave `SMTP_HOST` empty to skip email; notifications are still stored in the DB and shown in-app.

4. **APScheduler runs in-process** — In multi-worker deployments use `--workers 1`, or migrate the scheduler to Celery + Redis.

5. **Port 8000 may conflict** — If another Python process is using port 8000 (common in development), run `run.bat` as Administrator to force-kill it.

---

## Demo Data Notes

- All seeded institutions, complaints, and cases are **clearly fictional**.
- Data is labeled "DEMO DATA — Not actual AICTE records."
- Demo accounts are for development and testing only.
- **Remove all seed data and demo accounts before deploying to production.**

---

## Project Structure

```
aicte-complaint-dashboard/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/     # Route handlers
│   │   ├── core/                 # Config, DB, security
│   │   ├── matching/             # AI overlap engine
│   │   │   ├── overlap_engine.py
│   │   │   ├── institution_matcher.py
│   │   │   ├── complaint_matcher.py
│   │   │   └── normalizer.py
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic schemas
│   │   ├── services/             # Business logic
│   │   │   ├── conflict_service.py
│   │   │   ├── dashboard_service.py
│   │   │   └── ...
│   │   ├── db/seed.py            # Demo data seeder
│   │   └── tasks/scheduler.py    # APScheduler jobs
│   ├── alembic/versions/         # Database migrations
│   ├── tests/                    # Pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── public/logo.png           # AICTE logo
│   └── src/
│       ├── api/                  # Axios API clients
│       ├── components/           # Shared UI components
│       ├── layouts/              # AppLayout, AuthLayout
│       ├── pages/                # Route page components
│       │   ├── DashboardPage.tsx
│       │   ├── InstitutionProfilePage.tsx  # Digital Twin
│       │   ├── OverlapDetailPage.tsx       # Explainable AI view
│       │   ├── ConflictListPage.tsx        # Conflict warnings
│       │   └── ...
│       ├── routes/               # React Router config
│       └── types/                # TypeScript interfaces
├── docker-compose.yml
├── run.bat                       # One-click Windows launcher
├── .env.example
└── README.md
```

---

<p align="center">
  Built for <strong>Smart India Hackathon 2026</strong> · Problem Statement 26264<br/>
  © All India Council for Technical Education
</p>

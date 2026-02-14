# CareOps MVP: V3 Resilience & Traceability

Unified Operations Platform for high-trust service businesses (Barbers, Spas, Clinics). Focused on forensic traceability, safe human error recovery, and high-signal observability.

## 🚀 Quick Local Run

### 1. Prerequisites
- **Docker** (for PostgreSQL)
- **Python 3.11+**
- **Node.js 18+**

### 2. Database Setup
Spin up the PostgreSQL instance (mapped to port 5433 by default):
```bash
docker-compose up -d
```

### 3. Backend Setup
1. `cd backend`
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install: `pip install -r requirements.txt`
5. Configure `.env`: Copy `.env.example` to `.env` and update credentials.
6. Run Migrations (Optional if fresh start): `alembic upgrade head`
7. Start: `uvicorn app.main:app --reload`

### 4. Frontend Setup
1. `cd frontend`
2. `npm install`
3. `npm run dev`

---

## 🛡️ V3 Resilience Features
This version includes the **Forensic Traceability** and **Safe Recovery** layers:

- **Audit Timeline**: Every booking lifecycle event (inventory, emails, edits) is recorded.
- **Human Error Recovery**: Accidental cancellations can be restored with strict slot/inventory re-validation.
- **High-Signal Dashboard**: Priority-sorted pulse on failures and attention-required items.
- **Full Audit Trail**: `GET /api/bookings/{id}/history` provides a unified view of background and user actions.

## 🧪 Simulation & Audits
Run the survivability audit to verify your local setup:
```bash
python tests/survivability_audit.py
```
Or run the high-pressure **Chaos Day** simulation:
```bash
python tests/chaos_day.py
```

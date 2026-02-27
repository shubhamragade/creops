<div align="center">
  <h1>CareOps MVP: V3 Resilience & Traceability</h1>
  <p><strong>Unified Operations Platform for high-trust service businesses (Barbers, Spas, Clinics).</strong></p>
  <p><em>Focused on forensic traceability, safe human error recovery, and high-signal observability.</em></p>
</div>

---

## ⚠️ The Problem

High-trust service businesses (like clinics, premium spas, and barbershops) require flawless day-to-day operations to maintain their reputation and client trust. When human errors occur—such as accidental booking cancellations, inventory miscounts, or failed notification emails—existing management tools often lack transparency. These errors disappear into a "black box," making it extremely difficult to track down who did what and when, leading to operational chaos and lost revenue.

## 💡 How We Are Solving This

CareOps provides a safety net for human operations by acting as a high-signal, fully traceable platform:

1. **Forensic Traceability:** Every booking lifecycle event, inventory change, and email dispatch is recorded in an immutable audit timeline, completely eliminating the "black box" problem.
2. **Safe Human Error Recovery:** Accidental cancellations can be restored with strict slot and inventory re-validation, ensuring you can undo mistakes without causing double-bookings.
3. **High-Signal Observability:** A priority-sorted dashboard instantly surfaces operational failures (like failed emails or syntax errors), separating critical issues from background noise so staff know exactly what needs attention.

## 🛠️ Technology Stack

- **Backend:** Python 3.11+, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend:** Node.js 18+, React (Vite)
- **Infrastructure:** Docker (database), Alembic (migrations)

---

## 🚀 Quick Local Run

### 1. Prerequisites
- [Docker](https://www.docker.com/) (for PostgreSQL)
- **Python 3.11+**
- **Node.js 18+**

### 2. Database Setup
Spin up the PostgreSQL instance (mapped to port `5433` by default):
```bash
docker-compose up -d
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv

# Activate Virtual Environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

pip install -r requirements.txt

# Configure Environment
cp .env.example .env # (Update credentials as necessary)

# Run Database Migrations
alembic upgrade head

# Start Server
uvicorn app.main:app --reload
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

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

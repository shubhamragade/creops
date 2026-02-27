<br />
<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-blue.svg?logo=python&logoColor=white" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Next.js-14+-black.svg?logo=nextdotjs&logoColor=white" alt="Next.js 14+" />
  <img src="https://img.shields.io/badge/Docker-Enabled-2496ED.svg?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/Status-V3_MVP-success.svg?logo=checkmarx&logoColor=white" alt="Status" />

  <h1 align="center">CareOps: Business Operating System</h1>

  <p align="center">
    <strong>Operational Health • Inventory Automation • Staff Clarity • Owner Peace of Mind</strong><br />
    <em>Engineered for service-based businesses (Salons, Spas, Clinics)</em>
    <br /><br />
  </p>
</div>

---

## 🎯 The Business Challenge
Unlike typical booking apps that only act as a digital calendar, **CareOps** focuses on **Operational Health**. Service businesses struggle when the bridge between front-desk bookings and back-room operations breaks down. When a customer books a "Hair Coloring", does the salon actually have the "Red Dye" in stock? Are staff members seeing the right schedules? Are follow-ups happening on time?

When these systems disconnect, it results in double-bookings, stockouts as clients arrive, confused staff, and lost revenue.

## 💡 The CareOps Solution
CareOps acts as the "Brain" and "Robot Employee" of your operation, directly linking bookings to physical inventory, staff roles, and automated communications.

### 🔑 Core Workflows

**1. The "Perfect Booking" Flow (Inventory-Aware)**
CareOps doesn't just block time; it manages resources. When a client books a service:
* The system checks real-time inventory for required products.
* If stock is available, it auto-deducts the required units, creates the booking, and dispatches confirmation emails.
* If stock hits the defined low-threshold, an automated alert is immediately sent to the Owner to re-order.

**2. The "Staff Start" Flow (Secure & Contained)**
Staff management is built on privacy and simplicity:
* The Owner invites staff; the system generates a secure password and emails it directly (never returned via API).
* Upon login, role-based access control restricts the staff member to a dedicated portal (`/staff`) where they only see their assigned bookings and messages, protecting overall business data.

**3. The "Retention" Flow (Automated Follow-ups)**
CareOps acts as a "Robot Employee" running background cron jobs:
* It detects when a visit ended over an hour ago.
* It verifies if a follow-up has been sent.
* It automatically dispatches a "Thank You / Rate Us" email, closing the feedback loop without human intervention.

---

## 🏗️ System Architecture & Tech Stack

CareOps is built for resilience and async performance:
- **Frontend**: Next.js 14, React, TailwindCSS, Shadcn UI (Public Pages, Owner Dashboard, Staff Portal)
- **Backend**: FastAPI (Python), SQLModel/SQLAlchemy (High-performance API Router, Auth Middleware, Background Tasks)
- **Database**: PostgreSQL (Production operations and Persistence)
- **Services**: Resend API (Transactional Emails + Alerts), Python `BackgroundTasks` (Cron automation)

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Python 3.11+](https://www.python.org/downloads/)
- [Node.js 18+](https://nodejs.org/)

### 2. Database Initialization
Spin up the backend PostgreSQL container (exposes port `5433` by default):
```bash
docker-compose up -d
```

### 3. Backend Setup
```bash
# Navigate to the backend
cd backend

# Initialize and activate the virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies and configure environment
pip install -r requirements.txt
cp .env.example .env

# Apply database schemas
alembic upgrade head

# Launch the FastAPI server
uvicorn app.main:app --reload
```

### 4. Frontend Setup
```bash
# Navigate to the frontend
cd frontend

# Install Node modules and launch
npm install
npm run dev
```

---

## 🧪 Simulation & Auditing
CareOps ships with rigorous stress-testing scripts to guarantee system resilience:

**Run the Survivability Audit:**
```bash
python tests/survivability_audit.py
```

**Execute "Chaos Day" Simulation:**
Simulates high-pressure booking conflicts and cancellations.
```bash
python tests/chaos_day.py
```

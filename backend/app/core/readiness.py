"""
Core Readiness System

Provides:
1. Auto-seeding if DB empty (idempotent)
2. Startup readiness checks
3. Production mode detection
4. Reminder system status

No heavy frameworks. Simple and direct.
"""

import logging
import os
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import SessionLocal
from app.core.config import settings
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

def auto_seed_if_needed():
    """
    Auto-seed minimal demo data if DB is empty.
    Idempotent: safe to run multiple times.
    Non-destructive: skips if data exists.
    """
    db = SessionLocal()
    
    try:
        # Import models here to avoid circular imports
        from app.models.workspace import Workspace
        from app.models.user import User
        from app.models.service import Service
        from app.models.contact import Contact
        from app.models.booking import Booking, BookingStatus
        from app.models.inventory import InventoryItem
        
        # Check if already seeded
        user_count = db.query(User).count()
        
        if user_count > 0:
            logger.info("[AUTO-SEED] Skipped - data already exists")
            return
        
        logger.info("[AUTO-SEED] Empty database detected - seeding demo data...")
        
        # 1. Create Workspace
        workspace = Workspace(
            name="Demo Spa & Wellness",
            slug="demo-spa",
            contact_email="owner@demo-spa.com",
            timezone="Asia/Kolkata",
            is_active=True
        )
        db.add(workspace)
        db.flush()
        
        # 2. Create Owner User
        owner = User(
            email="owner@careops.com",
            hashed_password=get_password_hash("owner123"),
            role="owner",
            full_name="Demo Owner",
            workspace_id=workspace.id,
            is_active=True
        )
        db.add(owner)
        
        # 3. Create Staff User
        staff = User(
            email="staff@careops.com",
            hashed_password=get_password_hash("staff123"),
            role="staff",
            full_name="Demo Staff",
            workspace_id=workspace.id,
            is_active=True
        )
        db.add(staff)
        db.flush()
        
        # 4. Create Services
        massage_service = Service(
            workspace_id=workspace.id,
            name="Deep Tissue Massage",
            duration_minutes=60,
            availability={
                "mon": ["09:00-17:00"],
                "tue": ["09:00-17:00"],
                "wed": ["09:00-17:00"],
                "thu": ["09:00-17:00"],
                "fri": ["09:00-17:00"]
            }
        )
        facial_service = Service(
            workspace_id=workspace.id,
            name="Facial Treatment",
            duration_minutes=45,
            availability={
                "mon": ["10:00-16:00"],
                "tue": ["10:00-16:00"],
                "wed": ["10:00-16:00"],
                "thu": ["10:00-16:00"],
                "fri": ["10:00-16:00"]
            }
        )
        db.add_all([massage_service, facial_service])
        db.flush()
        
        # 5. Create Contacts
        contact1 = Contact(
            workspace_id=workspace.id,
            email="john.doe@example.com",
            full_name="John Doe",
            phone="+1234567890"
        )
        contact2 = Contact(
            workspace_id=workspace.id,
            email="jane.smith@example.com",
            full_name="Jane Smith",
            phone="+0987654321"
        )
        db.add_all([contact1, contact2])
        db.flush()
        
        # 6. Create Bookings
        now = datetime.now(timezone.utc)
        
        booking1 = Booking(
            workspace_id=workspace.id,
            service_id=massage_service.id,
            contact_id=contact1.id,
            start_time=now + timedelta(hours=3),
            end_time=now + timedelta(hours=4),
            status=BookingStatus.CONFIRMED.value
        )
        
        booking2 = Booking(
            workspace_id=workspace.id,
            service_id=facial_service.id,
            contact_id=contact2.id,
            start_time=now + timedelta(days=1, hours=2),
            end_time=now + timedelta(days=1, hours=2, minutes=45),
            status=BookingStatus.CONFIRMED.value
        )
        
        booking3 = Booking(
            workspace_id=workspace.id,
            service_id=massage_service.id,
            contact_id=contact1.id,
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=2, hours=-1),
            status=BookingStatus.COMPLETED.value
        )
        
        db.add_all([booking1, booking2, booking3])
        db.flush()
        
        # 7. Create Inventory Items
        oil = InventoryItem(
            workspace_id=workspace.id,
            name="Massage Oil",
            quantity=3,
            threshold=5
        )
        towels = InventoryItem(
            workspace_id=workspace.id,
            name="Towels",
            quantity=20,
            threshold=10
        )
        db.add_all([oil, towels])
        
        db.commit()
        
        logger.info("[AUTO-SEED] Created: 1 workspace, 2 users, 2 services, 3 bookings, 2 inventory items")
        
    except Exception as e:
        db.rollback()
        logger.error(f"[AUTO-SEED] Failed: {e}")
        # Don't raise - let system continue even if seed fails
    finally:
        db.close()


def check_system_readiness():
    """
    Check system readiness and return status dict.
    
    Returns:
        dict with keys: db_ok, owner_ok, staff_ok, services_ok, bookings_ok
    """
    db = SessionLocal()
    status = {
        "db_ok": False,
        "owner_ok": False,
        "staff_ok": False,
        "services_ok": False,
        "bookings_ok": False,
        "owner_email": None,
        "staff_email": None,
        "service_count": 0,
        "booking_count": 0
    }
    
    try:
        # Import models
        from app.models.user import User
        from app.models.service import Service
        from app.models.booking import Booking
        
        # Check DB connection
        db.execute(text("SELECT 1"))
        status["db_ok"] = True
        
        # Check owner user
        owner = db.query(User).filter(User.role == "owner").first()
        if owner:
            status["owner_ok"] = True
            status["owner_email"] = owner.email
        
        # Check staff user
        staff = db.query(User).filter(User.role == "staff").first()
        if staff:
            status["staff_ok"] = True
            status["staff_email"] = staff.email
        
        # Check services
        service_count = db.query(Service).count()
        if service_count > 0:
            status["services_ok"] = True
            status["service_count"] = service_count
        
        # Check bookings
        booking_count = db.query(Booking).count()
        if booking_count > 0:
            status["bookings_ok"] = True
            status["booking_count"] = booking_count
        
    except Exception as e:
        logger.error(f"[READINESS CHECK] Error: {e}")
    finally:
        db.close()
    
    return status


def check_production_mode():
    """
    Detect production mode based on environment variables.
    
    Returns:
        dict with service configuration status
    """
    services = {
        "email": settings.RESEND_API_KEY is not None,
        "scheduler": os.getenv("SCHEDULER_ACTIVE") is not None,
    }
    return services


def print_readiness_report():
    """
    Print startup readiness report to console.
    Clear, visible, actionable.
    """
    print("\n" + "="*60)
    print("CAREOPS STARTUP READINESS")
    print("="*60)
    
    # System checks
    status = check_system_readiness()
    
    def print_check(name, ok, detail=""):
        symbol = "[OK]" if ok else "[MISSING]"
        line = f"{symbol} {name}"
        if detail:
            line += f" ({detail})"
        print(line)
    
    print_check("Database connection", status["db_ok"])
    print_check("Owner user", status["owner_ok"], status.get("owner_email", ""))
    print_check("Staff user", status["staff_ok"], status.get("staff_email", ""))
    print_check("Services", status["services_ok"], f"{status['service_count']} configured")
    print_check("Bookings", status["bookings_ok"], f"{status['booking_count']} in system")
    
    # Overall status
    all_ok = all([
        status["db_ok"],
        status["owner_ok"],
        status["staff_ok"],
        status["services_ok"],
        status["bookings_ok"]
    ])
    
    print()
    if all_ok:
        print("CAREOPS DEMO READY")
    else:
        print("SYSTEM NOT READY - Missing components above")
    
    # External services
    print("\nExternal Services:")
    prod_services = check_production_mode()
    
    for service, configured in prod_services.items():
        status_text = "CONFIGURED" if configured else "DEMO MODE"
        print(f"  [{status_text}] {service.capitalize()}")
    
    # Reminder system check
    if not prod_services["scheduler"]:
        logger.info("[REMINDER SYSTEM] Reminder system inactive - demo mode")
    
    print("="*60 + "\n")


def check_reminder_system():
    """
    Check if reminder/cron system is active.
    Log clearly if inactive.
    """
    if not os.getenv("SCHEDULER_ACTIVE"):
        logger.info("[REMINDER SYSTEM] Reminder system inactive - demo mode")
        return False
    else:
        logger.info("[REMINDER SYSTEM] Scheduler active")
        return True

# SURGICAL FIX: Add missing GET endpoint for listing bookings
# This is additive - does not modify existing endpoints

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional

from app.api import deps
from app.schemas.booking import BookingCreate, BookingOut, BookingUpdate, ContactUpdate
from app.models.service import Service
from app.models.booking import Booking, BookingStatus
from app.models.contact import Contact
from app.models.inventory import InventoryItem
from app.models.workspace import Workspace
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services import email as email_service

router = APIRouter()

# SURGICAL ADD: Missing GET endpoint (was causing 405 error)
@router.get("/", response_model=List[BookingOut])
def list_bookings(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    """List all bookings for the current user's workspace."""
    bookings = db.query(Booking).filter(
        Booking.workspace_id == current_user.workspace_id
    ).order_by(Booking.start_time.desc()).all()
    return bookings

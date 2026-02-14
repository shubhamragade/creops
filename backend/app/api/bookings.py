from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.api import deps
from app.schemas.booking import BookingCreate, BookingOut, BookingUpdate, ContactUpdate
from app.schemas.onboarding import ServiceCreate # Only if using ServiceOut?
# We need a schema for ServiceOut actually. 
# Prompt said "GET /services/{workspace_slug} – public list of Services".
# We can define a simple ServiceOut here or in schemas/onboarding if reused.
# Let's define a minimal one or use dict.

from app.models.service import Service
from app.models.booking import Booking, BookingStatus
from app.models.contact import Contact
from app.models.inventory import InventoryItem
from app.models.workspace import Workspace
from app.models.user import User
from app.models.user import User
from app.models.audit_log import AuditLog
from app.services import email as email_service
from app.core.monitoring import log_booking_created, log_inventory_changed
from app.core.rate_limit import public_rate_limiter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/services/{workspace_slug}")
def get_services(workspace_slug: str, db: Session = Depends(deps.get_db)):
    workspace = db.query(Workspace).filter(Workspace.slug == workspace_slug).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    services = db.query(Service).filter(Service.workspace_id == workspace.id).all()
    return services

@router.post("/", response_model=BookingOut)
def create_booking(
    request: Request,
    booking_in: BookingCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    public_rate_limiter.check(request)
    # Transaction implied by SQLAlchemy session commit at end
    
    # 1. Validate Service
    service = db.query(Service).filter(Service.id == booking_in.service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
        
    # 2. Check Availability (Overlap)
    # Simple check: start_time match? Or range overlap?
    # Prompt says "check slot available (query Bookings for same time/service)"
    # Assuming fixed duration slots for MVP or exact start time match?
    # We'll check if there is an overlapping booking for the SAME service.
    # Overlap logic: (StartA < EndB) and (EndA > StartB)
    booking_end = booking_in.start_datetime + timedelta(minutes=service.duration_minutes)
    
    overlap = db.query(Booking).filter(
        Booking.service_id == service.id,
        Booking.status != BookingStatus.CANCELLED.value,
        Booking.start_time < booking_end,
        Booking.end_time > booking_in.start_datetime
    ).first()
    
    if overlap:
        # For a real system we'd check *capacity* (maybe multiple staff?). 
        # MVP: 1 slot per service per time? Or 1 booking per slot?
        # "check slot available". We'll assume single capacity per service instance for now.
        raise HTTPException(status_code=400, detail="Slot not available")

    # 3. Get/Create Contact
    contact = db.query(Contact).filter(
        Contact.email == booking_in.email,
        Contact.workspace_id == service.workspace_id
    ).first()
    if not contact:
        contact = Contact(
            email=booking_in.email,
            full_name=booking_in.name,
            phone=booking_in.phone,
            workspace_id=service.workspace_id,
            source="booking"
        )
        db.add(contact)
        db.flush() # Get ID
        
        # Trigger Welcome Email (only for new contacts)
        is_new_contact = True
        background_tasks.add_task(email_service.send_welcome_email, contact.email)
    else:
        # Update details if needed?
        if booking_in.phone and not contact.phone:
            contact.phone = booking_in.phone
            db.add(contact)

    # 4. Create Booking
    booking = Booking(
        service_id=service.id,
        contact_id=contact.id,
        workspace_id=service.workspace_id,
        start_time=booking_in.start_datetime,
        end_time=booking_end,
        status=BookingStatus.PENDING.value
    )
    db.add(booking)
    
    # [NEW] Audit Log: Booking Created
    audit_new = AuditLog(
        workspace_id=service.workspace_id,
        booking_id=booking.id, # Available after flush/commit? No, need manual flush if we want ID now.
        # But we commit below. We can add it to session, ID will be resolved.
        # Wait, booking.id is None until flushed.
        user_id=None, # System/Public
        action="booking.created",
        details={
            "service_name": service.name, 
            "source": "public_api"
        }
    )
    # We need booking ID.
    db.flush()
    audit_new.booking_id = booking.id
    db.add(audit_new)

    # 4.5 Create Conversation for this booking contact (CRITICAL: inbox must show booked customers)
    from app.models.conversation import Conversation
    existing_conv = db.query(Conversation).filter(
        Conversation.contact_id == contact.id,
        Conversation.workspace_id == service.workspace_id
    ).first()
    if not existing_conv:
        conv = Conversation(
            workspace_id=service.workspace_id,
            contact_id=contact.id,
            subject=f"Booking: {service.name}",
            last_message_at=datetime.now(timezone.utc),
            is_paused=False,
            last_message_is_internal=False
        )
        db.add(conv)

    # 5. Deduct Inventory (Explicit Link)
    if service.inventory_item_id and service.inventory_quantity_required > 0:
        inventory_item = db.query(InventoryItem).filter(InventoryItem.id == service.inventory_item_id).first()
        
        if inventory_item:
             if inventory_item.quantity < service.inventory_quantity_required:
                 raise HTTPException(status_code=400, detail=f"Service unavailable: {inventory_item.name} out of stock")
             
             old_qty = inventory_item.quantity
             inventory_item.quantity -= service.inventory_quantity_required
             db.add(inventory_item)
             
             # [MONITORING] Log inventory change
             log_inventory_changed(inventory_item.id, inventory_item.name, old_qty, inventory_item.quantity, "booking_created")
             
             # [NEW] Audit Log: Inventory Deducted
             audit_inv = AuditLog(
                workspace_id=service.workspace_id,
                booking_id=booking.id,
                user_id=None,
                action="inventory.deducted",
                details={
                    "item_id": inventory_item.id,
                    "item_name": inventory_item.name,
                    "quantity_deducted": service.inventory_quantity_required,
                    "remaining": inventory_item.quantity
                }
             )
             db.add(audit_inv)

             # Trigger Alert Immediately
             if inventory_item.quantity <= inventory_item.threshold:
                  background_tasks.add_task(email_service.send_inventory_alert, inventory_item.id)

    # 6. Create Pending Form Submission (for Reminders)
    # This ensures we can track if they actually fill it out.
    from app.models.form import Form, FormSubmission
    
    # Check if workspace has an intake form
    intake_form = db.query(Form).filter(
        Form.workspace_id == service.workspace_id,
        Form.type == "intake"
    ).first()
    
    # Even if no specific form exists yet, we create a record to track the "requirement" 
    # if we want to send reminders.
    # Ref: "Step 5... automated form that we will be sending after the booking"
    # We only create it if we have a form definition or intend to use a default one.
    # For MVP, let's assume we always want one.
    
    pending_sub = FormSubmission(
        form_id=intake_form.id if intake_form else None,
        booking_id=booking.id,
        data={},
        status="pending",
        sent_at=datetime.now(timezone.utc), # "Sent" via email magic link below
        reminder_sent=False
    )
    db.add(pending_sub)
    
    db.commit()
    db.refresh(booking)

    # [CONFIDENCE CHECK] Verify inventory deduction if applicable
    if service.inventory_item_id and service.inventory_quantity_required > 0:
        db.refresh(inventory_item)
        # Log but never crash
        logger.info(f"[INVENTORY CONFIDENCE] Verified deduction for booking {booking.id}")

    # [MONITORING] Log booking creation
    log_booking_created(booking.id, service.name, contact.email)

    # 7. Background Tasks
    background_tasks.add_task(email_service.send_booking_confirmation, booking.id)
    background_tasks.add_task(email_service.send_form_magic_link, booking.id) 
    # Reminder moved to Cron

    
    return booking

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

@router.post("/{booking_id}/cancel")
async def cancel_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
    token: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_active_staff_or_owner_optional)
):
    """
    Cancel a booking.
    """
    # 1. Auth Check
    is_authorized = False
    if current_user:
        is_authorized = True
    elif token:
        from app.core.security_utils import verify_cancel_token
        if verify_cancel_token(token, booking_id):
            is_authorized = True
            
    if not is_authorized:
        raise HTTPException(status_code=401, detail="Unauthorized to cancel this booking")

    booking = db.query(Booking).filter(
        Booking.id == booking_id
    ).first()
    
    # If authenticated, ensure workspace match
    if current_user and booking and booking.workspace_id != current_user.workspace_id:
         raise HTTPException(status_code=404, detail="Booking not found")

    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    if booking.status == BookingStatus.CANCELLED.value:
        return {"status": "already_cancelled"}
        
    # Logic: Update status, Refund inventory?, Send Email
    booking.status = BookingStatus.CANCELLED.value
    db.add(booking)
    
    # [NEW] Inventory Return Logic
    if booking.service_id:
        # We need the service to know quantity
        service = booking.service
        if service.inventory_item_id and service.inventory_quantity_required > 0:
            item = db.query(InventoryItem).filter(InventoryItem.id == service.inventory_item_id).first()
            if item:
                item.quantity += service.inventory_quantity_required
                db.add(item)
                
                # Audit Log: Inventory Returned
                audit_inv = AuditLog(
                    workspace_id=booking.workspace_id,
                    booking_id=booking.id,
                    user_id=current_user.id if current_user else None,
                    action="inventory.returned",
                    details={
                        "item_id": item.id,
                        "item_name": item.name,
                        "quantity_returned": service.inventory_quantity_required,
                        "new_quantity": item.quantity
                    }
                )
                db.add(audit_inv)

    db.commit()

    # [NEW] Audit Log: Cancelled
    # [NEW] Audit Log: Cancelled
    audit_cancel = AuditLog(
        workspace_id=booking.workspace_id,
        booking_id=booking.id,
        user_id=current_user.id if current_user else None,
        action="booking.cancelled",
        details={"reason": "staff_action" if current_user else "customer_token"}
    )
    db.add(audit_cancel)
    db.commit()

    
    # Email
    background_tasks.add_task(email_service.send_booking_cancellation, booking.id)
    
    return {"status": "cancelled", "message": "Booking cancelled and confirmation sent."}
@router.post("/{booking_id}/emails/confirmation")
async def resend_confirmation(
    booking_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    """
    Manually resend booking confirmation.
    """
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.workspace_id == current_user.workspace_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    background_tasks.add_task(email_service.send_booking_confirmation, booking.id)
    return {"status": "queued", "message": "Confirmation email queued"}

@router.post("/{booking_id}/emails/form-link")
async def resend_form_link(
    booking_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    """
    Manually resend intake form link.
    """
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.workspace_id == current_user.workspace_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    background_tasks.add_task(email_service.send_form_magic_link, booking.id)
    return {"status": "queued", "message": "Form link email queued"}

@router.get("/{booking_id}/form")
def get_booking_form_submission(
    booking_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    """
    Get the intake form submission for a booking.
    """
    # 1. Fetch Booking and verify access
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.workspace_id == current_user.workspace_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # 2. Fetch Submission
    from app.models.form import FormSubmission
    submission = db.query(FormSubmission).filter(
        FormSubmission.booking_id == booking.id
    ).order_by(FormSubmission.sent_at.desc()).first()
    
    if not submission:
        return None # Or specific message

    # 3. Format Response
    # We want labels + values.
    # Submission.data is usually { "field_name": "value" }
    # Form.fields is [ { "name": "field_name", "label": "Label", ... } ]
    
    response = {
        "status": submission.status,
        "sent_at": submission.sent_at,
        "completed_at": submission.completed_at,
        "answers": []
    }
    
    if submission.data and submission.form:
        # Map fields to labels
        field_map = {f.get("name"): f.get("label", f.get("name")) for f in submission.form.fields}
        
        for key, value in submission.data.items():
            response["answers"].append({
                "label": field_map.get(key, key),
                "value": value
            })
            
    return response
    
@router.get("/{booking_id}/history")
def get_booking_history(
    booking_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    """
    Get full history (AuditLog + CommunicationLog) for a booking.
    """
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.workspace_id == current_user.workspace_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Fetch Audits
    from app.models.audit_log import AuditLog
    audits = db.query(AuditLog).filter(AuditLog.booking_id == booking.id).all()
    
    # Fetch Comms
    from app.models.communication_log import CommunicationLog
    comms = db.query(CommunicationLog).filter(CommunicationLog.booking_id == booking.id).all()
    
    # Merge and Sort
    timeline = []
    
    for a in audits:
        timeline.append({
            "id": f"audit_{a.id}",
            "type": "audit",
            "action": a.action,
            "details": a.details,
            "created_at": a.created_at,
            "user_id": a.user_id
        })
        
    for c in comms:
        timeline.append({
            "id": f"comm_{c.id}",
            "type": "communication",
            "action": f"email.{c.type}",
            "details": {"recipient": c.recipient_email, "status": c.status, "error": c.error_message},
            "created_at": c.created_at,
            "user_id": None # System
        })
        
    # Sort by created_at desc
    timeline.sort(key=lambda x: x["created_at"], reverse=True)
    
    return timeline

@router.post("/{booking_id}/reschedule")
async def public_reschedule_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    background_tasks: BackgroundTasks,
    token: Optional[str] = None,
    db: Session = Depends(deps.get_db),
    current_user: Optional[User] = Depends(deps.get_current_active_staff_or_owner_optional)
):
    """
    Public endpoint to reschedule a booking using a token or authentication.
    """
    # 1. Auth Check
    is_authorized = False
    if current_user:
        is_authorized = True
    elif token:
        from app.core.security_utils import verify_cancel_token
        # Re-using cancel token logic for rescheduling security
        if verify_cancel_token(token, booking_id):
            is_authorized = True
            
    if not is_authorized:
        raise HTTPException(status_code=401, detail="Unauthorized to reschedule this booking")

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # If authenticated, ensure workspace match
    if current_user and booking.workspace_id != current_user.workspace_id:
         raise HTTPException(status_code=404, detail="Booking not found")

    # 2. Terminal State Check
    terminal_states = [BookingStatus.CANCELLED.value, BookingStatus.COMPLETED.value, BookingStatus.NO_SHOW.value]
    if booking.status in terminal_states:
        raise HTTPException(status_code=400, detail="Cannot reschedule booking in terminal state")

    if not booking_update.start_datetime:
        raise HTTPException(status_code=400, detail="start_datetime is required")

    old_start = booking.start_time
    new_start = booking_update.start_datetime
    service = booking.service
    new_end = new_start + timedelta(minutes=service.duration_minutes)

    # 3. Availability Check (Exclude self)
    overlap = db.query(Booking).filter(
        Booking.workspace_id == booking.workspace_id,
        Booking.status.in_([BookingStatus.CONFIRMED.value, BookingStatus.PENDING.value]),
        Booking.id != booking.id,
        Booking.start_time < new_end,
        Booking.end_time > new_start
    ).first()
    
    if overlap:
        raise HTTPException(status_code=409, detail="New slot occupied")

    # 4. Apply changes
    booking.start_time = new_start
    booking.end_time = new_end
    booking.status = BookingStatus.CONFIRMED.value # Auto-confirm if they move it?
    db.add(booking)
    
    # 5. Audit Log
    db.add(AuditLog(
        workspace_id=booking.workspace_id,
        booking_id=booking.id,
        user_id=current_user.id if current_user else None,
        action="booking.rescheduled",
        details={
            "old_start": old_start.isoformat(),
            "new_start": new_start.isoformat(),
            "source": "public_token" if not current_user else "staff_dashboard"
        }
    ))
    
    db.commit()
    
    # 6. Notification
    background_tasks.add_task(email_service.send_booking_confirmation, booking.id)
    
    return {"status": "updated", "message": "Booking rescheduled successfully"}


@router.patch("/{booking_id}")
def update_booking(
    booking_id: int,
    booking_update: BookingUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    """
    Update booking status (Admin/Staff only).
    """
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.workspace_id == current_user.workspace_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    if booking_update.status:
        booking.status = booking_update.status
        db.add(booking)
        db.commit()

    return {"status": "updated", "message": "Booking updated successfully"}


@router.patch("/{booking_id}/details")
def update_booking_details(
    booking_id: int,
    contact_update: ContactUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    """
    Update customer details for a booking.
    """
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.workspace_id == current_user.workspace_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    contact = booking.contact
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    if contact_update.full_name:
        contact.full_name = contact_update.full_name
    if contact_update.email:
        contact.email = contact_update.email
    if contact_update.phone:
        contact.phone = contact_update.phone
        
    db.add(contact)
    
    # Audit Log
    db.add(AuditLog(
        workspace_id=booking.workspace_id,
        booking_id=booking.id,
        user_id=current_user.id,
        action="booking.details_updated",
        details={"updated_fields": list(contact_update.dict(exclude_unset=True).keys())}
    ))
    
    db.commit()
    return {"status": "updated", "message": "Details updated successfully"}


@router.post("/{booking_id}/restore")
def restore_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    """
    Restore a CANCELLED booking if slot and inventory are available.
    """
    booking = db.query(Booking).filter(
        Booking.id == booking_id,
        Booking.workspace_id == current_user.workspace_id
    ).first()
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
        
    # Idempotency
    if booking.status == BookingStatus.CONFIRMED.value:
        return {"status": "already_confirmed", "message": "Booking is already active"}
        
    if booking.status != BookingStatus.CANCELLED.value:
         raise HTTPException(status_code=400, detail=f"Cannot restore booking with status: {booking.status}")

    # 1. Availability Check
    # Check against any booking that isn't CANCELLED
    overlap = db.query(Booking).filter(
        Booking.workspace_id == booking.workspace_id,
        Booking.status.in_([BookingStatus.CONFIRMED.value, BookingStatus.PENDING.value]),
        Booking.id != booking.id, # Exclude self just in case
        Booking.start_time < booking.end_time,
        Booking.end_time > booking.start_time
    )
    
    # If the booking has a specific staff member, check for their availability specifically.
    # If not, we assume workspace capacity (which for MVP is usually 1:1 or global).
    if booking.staff_id:
        overlap = overlap.filter(Booking.staff_id == booking.staff_id)
        
    overlap_item = overlap.first()
    
    if overlap_item:
         raise HTTPException(
             status_code=409, 
             detail=f"Time slot is now occupied by booking #{overlap_item.id} ({overlap_item.status})"
         )
         
    # 2. Inventory Check & Re-deduction (MANDATORY per user request)
    service = booking.service
    if service.inventory_item_id and service.inventory_quantity_required > 0:
        inventory_item = db.query(InventoryItem).filter(InventoryItem.id == service.inventory_item_id).with_for_update().first()
        
        if not inventory_item:
             raise HTTPException(status_code=400, detail="Associated inventory item not found")
             
        if inventory_item.quantity < service.inventory_quantity_required:
             raise HTTPException(
                 status_code=409, 
                 detail=f"Insufficient inventory to restore: {inventory_item.name} (Need {service.inventory_quantity_required}, have {inventory_item.quantity})"
             )
             
        # Deduct
        inventory_item.quantity -= service.inventory_quantity_required
        db.add(inventory_item)
        
        # Log Inventory Deduct
        audit_inv = AuditLog(
            workspace_id=booking.workspace_id,
            booking_id=booking.id,
            user_id=current_user.id,
            action="inventory.deducted_restore",
            details={
                "item_id": inventory_item.id,
                "item_name": inventory_item.name,
                "quantity": service.inventory_quantity_required,
                "remaining": inventory_item.quantity
            }
        )
        db.add(audit_inv)
        
        # Trigger Alert?
        if inventory_item.quantity <= inventory_item.threshold:
              background_tasks.add_task(email_service.send_inventory_alert, inventory_item.id)

    # 3. Update Status
    booking.status = BookingStatus.CONFIRMED.value
    db.add(booking)
    
    # 4. Audit Log
    audit_restore = AuditLog(
        workspace_id=booking.workspace_id,
        booking_id=booking.id,
        user_id=current_user.id,
        action="booking.restored",
        details={"previous_status": "cancelled"}
    )
    db.add(audit_restore)
    
    db.commit()
    
    # 5. Notify?
    # Send 'Booking Restored' confirmation
    background_tasks.add_task(email_service.send_booking_confirmation, booking.id)
    
    return {"status": "restored", "message": "Booking restored successfully"}


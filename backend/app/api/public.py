from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date, timezone
from typing import List, Optional, Any
from pydantic import BaseModel, EmailStr
import pytz

from app.api import deps
from app.models.service import Service
from app.models.booking import Booking, BookingStatus
from app.models.workspace import Workspace
from app.models.contact import Contact
from app.models.conversation import Conversation, Message
from app.models.conversation import Conversation, Message
from app.models.form import Form, FormSubmission
from app.models.inventory import InventoryItem
from app.services import email as email_service
from app.core.monitoring import log_booking_created # Reuse generic logging? Or add new.
from app.core.rate_limit import public_rate_limiter

router = APIRouter()

class ContactFormSubmit(BaseModel):
    workspace_id: int
    name: str
    email: EmailStr
    message: str
    phone: Optional[str] = None

@router.post("/contact")
def submit_contact_form(
    request: Request,
    form_in: ContactFormSubmit,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    public_rate_limiter.check(request)
    # 1. Verify Workspace
    workspace = db.query(Workspace).filter(Workspace.id == form_in.workspace_id).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    # 2. Find or Create Contact
    contact = db.query(Contact).filter(
        Contact.email == form_in.email,
        Contact.workspace_id == form_in.workspace_id
    ).first()
    
    is_new_contact = False
    if not contact:
        is_new_contact = True
        contact = Contact(
            workspace_id=form_in.workspace_id,
            email=form_in.email,
            full_name=form_in.name,
            phone=form_in.phone,
            source="form"
        )
        db.add(contact)
        db.flush()
    else:
        # Update name/phone if missing?
        if form_in.name and not contact.full_name:
            contact.full_name = form_in.name
            db.add(contact)
            
    # 3. Create Conversation / Message
    # Check if active conversation exists? 
    # For now, append to latest or create new if closed.
    # Simple logic: Always create new message in a conversation.
    # Find latest conversation
    conversation = db.query(Conversation).filter(
        Conversation.contact_id == contact.id,
        Conversation.workspace_id == form_in.workspace_id
    ).order_by(Conversation.last_message_at.desc()).first()
    
    if not conversation:
        conversation = Conversation(
            workspace_id=form_in.workspace_id,
            contact_id=contact.id,
            subject="New Inquiry", # Or from message snippet
            last_message_at=datetime.utcnow(),
            is_paused=False
        )
        db.add(conversation)
        db.flush()
    else:
        conversation.last_message_at = datetime.utcnow()
        conversation.is_paused = False # Unpause if customer replies
        conversation.last_message_is_internal = False
        db.add(conversation)

    message = Message(
        conversation_id=conversation.id,
        content=form_in.message,
        sender_email=form_in.email,
        is_internal=False
    )
    db.add(message)
    db.commit()
    
    # 4. Welcome email — only for new contacts (hackathon brief: "New contact → welcome message")
    if is_new_contact:
        # User request: "Reverse Booking Flow" -> Send Booking Link in Welcome Email
        # Construct booking URL
        from app.core.config import settings
        booking_url = f"{settings.FRONTEND_URL}/book/{workspace.slug}"
        background_tasks.add_task(email_service.send_welcome_email, contact.email, booking_url)

    # 4. Notify Owner (Email)
    background_tasks.add_task(email_service.notify_owner_new_message, message.id)
    
    return {"status": "submitted"}

@router.get("/workspace/{slug}")
def get_workspace_public_config(
    slug: str,
    db: Session = Depends(deps.get_db)
):
    workspace = db.query(Workspace).filter(Workspace.slug == slug, Workspace.is_active == True).first()
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
        
    services = db.query(Service).filter(Service.workspace_id == workspace.id).all()
    
    return {
        "id": workspace.id,
        "name": workspace.name,
        "address": workspace.address,
        "contact_email": workspace.contact_email,
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "duration_minutes": s.duration_minutes
            } for s in services
        ]
    }

@router.get("/services/{service_id}/availability", response_model=List[str])
def get_service_availability(
    service_id: int,
    query_date: date = Query(..., alias="date"),
    timezone: str = Query("UTC"), # Default to UTC if not provided, or fetch from workspace
    db: Session = Depends(deps.get_db)
):
    """
    Get available time slots for a service on a specific date.
    Returns a list of start times (e.g. ["09:00", "09:30"]).
    """
    # 1. Fetch Service and Workspace
    service = db.query(Service).filter(Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    workspace = db.query(Workspace).filter(Workspace.id == service.workspace_id).first()
    # If workspace has timezone setting, use it. Otherwise use param or UTC.
    # checking workspace model next, assuming generic for now.
    ws_tz_str = timezone
    # if hasattr(workspace, 'timezone') and workspace.timezone:
    #     ws_tz_str = workspace.timezone
    
    try:
        tz = pytz.timezone(ws_tz_str)
    except pytz.UnknownTimeZoneError:
        tz = pytz.UTC

    # 2. Check Inventory Level (Crucial Gap Fill)
    # If service requires inventory and it's out of stock, zero slots available.
    if service.inventory_item_id and service.inventory_quantity_required > 0:
        inventory_item = db.query(InventoryItem).filter(InventoryItem.id == service.inventory_item_id).first()
        if not inventory_item or inventory_item.quantity < service.inventory_quantity_required:
            # Out of stock. Return empty list immediately.
            return []

    # 3. Determine Weekday (0=Monday, 6=Sunday)
    weekday_map = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    day_str = weekday_map[query_date.weekday()]
    
    # 3. Get Availability for Weekday
    # availability format: {"mon": ["09:00-17:00"], "tue": ...}
    availability = service.availability or {}
    day_slots = availability.get(day_str, [])
    
    if not day_slots:
        return []

    # 4. Generate All Possible Slots
    potential_slots = []
    duration = service.duration_minutes
    
    for time_range in day_slots:
        try:
            start_str, end_str = time_range.split("-")
            
            # Create datetime objects for the selected date + time in the target timezone
            # Format: HH:MM
            start_dt = datetime.strptime(f"{query_date} {start_str}", "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(f"{query_date} {end_str}", "%Y-%m-%d %H:%M")
            
            # Localize
            start_dt = tz.localize(start_dt)
            end_dt = tz.localize(end_dt)
            
            current_slot = start_dt
            while current_slot + timedelta(minutes=duration) <= end_dt:
                potential_slots.append(current_slot)
                current_slot += timedelta(minutes=duration)
                
        except ValueError:
            continue # Skip malformed ranges

    if not potential_slots:
        return []

    # 5. Query Existing Bookings for Conflicts
    # We need to check range [DayStart, DayEnd] in UTC to query DB efficiently
    # Or just check if any booking overlaps each slot.
    # Optimization: Query all bookings for this service on this day.
    
    # Define "Day" in UTC terms to cover all timezones? 
    # Or just convert potential slots to UTC and check.
    
    # Range of interesting time: Min Slot Start -> Max Slot End
    min_time = min(potential_slots)
    max_time = max(potential_slots) + timedelta(minutes=duration)
    
    # Convert to UTC for DB query
    min_time_utc = min_time.astimezone(pytz.UTC)
    max_time_utc = max_time.astimezone(pytz.UTC)
    
    conflicting_bookings = db.query(Booking).filter(
        Booking.service_id == service.id,
        Booking.status != BookingStatus.CANCELLED.value,
        Booking.end_time > min_time_utc, # Overlap logic
        Booking.start_time < max_time_utc
    ).all()
    
    # 6. Filter Slots
    final_slots = []
    for slot_start in potential_slots:
        slot_end = slot_start + timedelta(minutes=duration)
        slot_start_utc = slot_start.astimezone(pytz.UTC)
        slot_end_utc = slot_end.astimezone(pytz.UTC)
        
        is_free = True
        for booking in conflicting_bookings:
            # Check overlap: (StartA < EndB) and (EndA > StartB)
            # booking.start_time is already UTC (from DB)
            if (slot_start_utc < booking.end_time) and (slot_end_utc > booking.start_time):
                is_free = False
                break
        
        if is_free:
            # Return time string in requested timezone
            final_slots.append(slot_start.strftime("%H:%M"))
            
    return final_slots


@router.get("/bookings/{booking_id}")
def get_public_booking(
    booking_id: int,
    token: str,
    db: Session = Depends(deps.get_db)
):
    """
    Get booking details publicly if token is valid.
    Used for Reschedule/Cancel pages.
    """
    from app.core.security_utils import verify_cancel_token
    if not verify_cancel_token(token, booking_id):
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return {
        "id": booking.id,
        "service_name": booking.service.name,
        "service_id": booking.service_id,
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "status": booking.status,
        "workspace_name": booking.workspace.name,
        "workspace_slug": booking.workspace.slug,
        "customer_name": booking.contact.full_name if booking.contact else "Guest"
    }


# --- INTAKE FORM ENDPOINTS ---

@router.get("/bookings/{booking_id}/intake")
def get_booking_intake(
    booking_id: int,
    token: Optional[str] = None, # Future proofing
    db: Session = Depends(deps.get_db)
):
    """
    Get intake form details for a booking.
    Public endpoint.
    """
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Verify state (Optional)
    # if booking.status == BookingStatus.CANCELLED.value:
    #      raise HTTPException(status_code=400, detail="Booking is cancelled")

    service = booking.service
    contact = booking.contact
    workspace = booking.workspace
    
    # 1. Check if Service has a form? 
    # Current model doesn't link Service -> Form explicitly except maybe via name convention or generic "Intake"?
    # For MVP, we assume a GLOBAL or SERVICE-SPECIFIC intake form mechanism.
    # Let's check if there's an "Intake Form" in the workspace.
    
    form = db.query(Form).filter(
        Form.workspace_id == workspace.id,
        Form.type == "intake" # We might need to standardize this type
    ).first()
    
    # If no specific form, return basic contact details confirmation?
    # Or create a default one on the fly?
    # Better: If no form, we can't do intake.
    if not form:
        # Fallback: Check for "Contact Form" or generic
        form = db.query(Form).filter(Form.workspace_id == workspace.id, Form.type == "contact").first()
    
    if not form:
         # Hard fail or generic empty?
         # Let's return a generic schema if none found to avoid blocking.
         fields = [{"name": "notes", "type": "textarea", "label": "Anything we should know?", "required": False}]
         form_name = "Intake Form"
    else:
         fields = form.fields
         form_name = form.name

    # Pre-fill logic:
    # If the form has fields that match contact attributes, pre-fill them.
    # We'll creating a "pre_filled_answers" dictionary.
    pre_filled_answers = {}
    if contact:
        # Map common field names to contact attributes
        # Heuristic matching: keys are lowercase version of label or name
        for field in fields:
            f_name = field.get("name", "").lower()
            f_label = field.get("label", "").lower()
            
            val = None
            if "name" in f_name or "name" in f_label:
                val = contact.full_name
            elif "email" in f_name or "email" in f_label:
                val = contact.email
            elif "phone" in f_name or "phone" in f_label:
                val = contact.phone
            elif "address" in f_name or "address" in f_label:
                val = getattr(contact, "address", "")
            
            if val:
                pre_filled_answers[field["name"]] = val

    return {
        "booking_id": booking.id,
        "customer_name": contact.full_name,
        "service_name": service.name,
        "date_time": booking.start_time, # Frontend handles formatting
        "workspace_name": workspace.name,
        "form": {
            "name": form_name,
            "fields": fields,
            "google_form_url": form.google_form_url if form else None,
            "pre_filled_answers": pre_filled_answers
        },
        "status": booking.status
    }

class IntakeSubmit(BaseModel):
    answers: dict

@router.post("/bookings/{booking_id}/intake")
def submit_booking_intake(
    request: Request,
    booking_id: int,
    submission: IntakeSubmit,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """
    Submit intake form.
    """
    public_rate_limiter.check(request)
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    # Find the form again to link it? 
    # We will just store it as a generic submission linked to the booking.
    # Ideally we know WHICH form ID it was, but for now we link to Booking.
    
    # Find existing pending submission for this booking
    # (Created during booking creation in bookings.py)
    form_sub = db.query(FormSubmission).filter(
        FormSubmission.booking_id == booking.id
    ).first()
    
    if form_sub:
        # Update existing
        form_sub.data = submission.answers
        form_sub.status = "completed"
        form_sub.completed_at = datetime.now(timezone.utc)
        # Verify form_id is linked if missing (should be there from creation)
        if not form_sub.form_id:
             # Try to link intake form now
             form = db.query(Form).filter(
                Form.workspace_id == booking.workspace_id,
                Form.type == "intake"
             ).first()
             if form:
                 form_sub.form_id = form.id
    else:
        # Fallback: Create new if missing (e.g. old bookings)
        # Try to find 'Intake' form to link
        form = db.query(Form).filter(
            Form.workspace_id == booking.workspace_id,
            Form.type == "intake"
        ).first()
        
        form_sub = FormSubmission(
            form_id=form.id if form else None,
            booking_id=booking.id,
            data=submission.answers,
            status="completed",
            sent_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc)
        )
        db.add(form_sub)
    
    db.commit()
    
    # Create Inbox Message for visibility
    if booking.contact:
        contact = booking.contact
        conversation = db.query(Conversation).filter(
            Conversation.contact_id == contact.id,
            Conversation.workspace_id == booking.workspace_id
        ).order_by(Conversation.last_message_at.desc()).first()
        
        if not conversation:
            conversation = Conversation(
                workspace_id=booking.workspace_id,
                contact_id=contact.id,
                subject=f"Intake Completed: {booking.service.name}",
                last_message_at=datetime.utcnow(),
                is_paused=False
            )
            db.add(conversation)
            db.flush()
        else:
            conversation.last_message_at = datetime.utcnow()
            conversation.is_paused = False
            conversation.last_message_is_internal = False
            db.add(conversation)
            
        # Format
        msg_lines = [f"Intake form completed for booking #{booking.id}"]
        for k, v in submission.answers.items():
             msg_lines.append(f"{k}: {v}")
             
        message = Message(
            conversation_id=conversation.id,
            content="\n".join(msg_lines),
            sender_email=contact.email,
            is_internal=False
        )
        db.add(message)
        db.commit()

    # Notify Owner
    # "New Intake Received"
    background_tasks.add_task(email_service.notify_owner_intake, booking.id)

    # Notify Customer (Confirmation)
    if form_sub and form_sub.id:
        background_tasks.add_task(email_service.send_intake_received_email, form_sub.id)
    

# --- STANDALONE PUBLIC FORM ENDPOINTS ---

@router.get("/forms/{form_id}")
def get_public_form(
    form_id: int,
    db: Session = Depends(deps.get_db)
):
    """
    Get a specific form by ID for public display (Lead Capture).
    """
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
        
    workspace = db.query(Workspace).filter(Workspace.id == form.workspace_id).first()
    
    return {
        "id": form.id,
        "name": form.name,
        "fields": form.fields,
        "google_form_url": form.google_form_url,
        "workspace_name": workspace.name if workspace else "CareOps",
        "workspace_slug": workspace.slug if workspace else None
    }

@router.post("/forms/{form_id}/submit")
def submit_public_form(
    request: Request,
    form_id: int,
    submission: IntakeSubmit,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db)
):
    """
    Submit a standalone public form.
    Creates a Contact and sends Welcome Email with Booking Link.
    """
    public_rate_limiter.check(request)
    form = db.query(Form).filter(Form.id == form_id).first()
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
        
    # 1. Extract Contact Details (Name/Email/Phone) if present
    answers = submission.answers
    email = None
    name = None
    phone = None
    
    # Heuristic extraction
    for key, val in answers.items():
        k = key.lower()
        if "email" in k: email = val
        if "name" in k: name = val
        if "phone" in k: phone = val
        
    contact = None
    is_new = False
    
    # 2. Create/Find Contact
    if email:
        contact = db.query(Contact).filter(Contact.email == email, Contact.workspace_id == form.workspace_id).first()
        if not contact:
            is_new = True
            contact = Contact(
                workspace_id=form.workspace_id,
                email=email,
                full_name=name,
                phone=phone,
                source="public_form"
            )
            db.add(contact)
            db.flush()
        else:
            # Update info if missing
            if name and not contact.full_name: 
                contact.full_name = name
                db.add(contact)
    
    # 3. Store Submission
    # Create submission record even if not linked to booking
    form_sub = FormSubmission(
        form_id=form.id,
        booking_id=None, # Standalone
        data=answers,
        status="completed",
        sent_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc)
    )
    db.add(form_sub)
    
    # 4. Create Inbox Message (So it appears in dashboard)
    if contact:
        # Find or create conversation
        conversation = db.query(Conversation).filter(
            Conversation.contact_id == contact.id,
            Conversation.workspace_id == form.workspace_id
        ).order_by(Conversation.last_message_at.desc()).first()
        
        if not conversation:
            conversation = Conversation(
                workspace_id=form.workspace_id,
                contact_id=contact.id,
                subject=f"New Submission: {form.name}",
                last_message_at=datetime.utcnow(),
                is_paused=False
            )
            db.add(conversation)
            db.flush() # Get ID
        else:
            conversation.last_message_at = datetime.utcnow()
            conversation.is_paused = False
            conversation.last_message_is_internal = False
            db.add(conversation)
            
        # Format message content
        msg_lines = [f"New submission for form: {form.name}"]
        for k, v in answers.items():
            msg_lines.append(f"{k}: {v}")
        
        message = Message(
            conversation_id=conversation.id,
            content="\n".join(msg_lines),
            sender_email=contact.email,
            is_internal=False
        )
        db.add(message)
        db.commit() # Commit before background task
        
        # 5. Notify Owner (Email)
        background_tasks.add_task(email_service.notify_owner_new_message, message.id)

    else:
        db.commit()

    # 6. Trigger "Reverse Flow" Email (Welcome)
    if contact:
        workspace = db.query(Workspace).filter(Workspace.id == form.workspace_id).first()
        from app.core.config import settings
        booking_url = f"{settings.FRONTEND_URL}/book/{workspace.slug}"
        background_tasks.add_task(email_service.send_welcome_email, contact.email, booking_url)
        
    return {"status": "success", "message": "Form submitted"}

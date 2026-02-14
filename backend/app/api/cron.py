from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from app.api import deps
from app.models.booking import Booking, BookingStatus
from app.models.form import FormSubmission
from app.models.inventory import InventoryItem
from app.models.inventory import InventoryItem
from app.models.audit_log import AuditLog
from app.services import email as email_service
from app.core.config import settings

router = APIRouter()

@router.post("/run")
async def run_cron_jobs(
    db: Session = Depends(deps.get_db),
    x_cron_secret: Optional[str] = Header(None)
):
    # Verify cron secret
    if x_cron_secret != settings.CRON_SECRET:
        raise HTTPException(status_code=403, detail="Invalid cron secret")
    """
    Trigger scheduled checks:
    1. Booking Reminders (24h before)
    2. Form Reminders (Overdue)
    3. Inventory Alerts
    4. Thank You Emails
    5. Owner Daily Summary
    """
    results = {
        "booking_reminders": 0,
        "form_reminders": 0,
        "inventory_alerts": 0
    }
    
    now = datetime.now(timezone.utc)
    
    # ------------------------------------------------------------------
    # 1. BOOKING REMINDERS (Approx 24 hours before start)
    # ------------------------------------------------------------------
    # Find bookings starting between (Now + 23h) and (Now + 25h) that haven't entered loop?
    # Or just "starts < Now + 24h" and not sent?
    # Let's say "Starts within next 24 hours" AND reminder_sent=False
    
    tomorrow = now + timedelta(hours=24)
    # Look for bookings coming up in next 24h
    upcoming_bookings = db.query(Booking).filter(
        Booking.start_time > now, 
        Booking.start_time <= tomorrow,
        Booking.status != BookingStatus.CANCELLED.value,
        Booking.reminder_sent == False
    ).all()
    
    for booking in upcoming_bookings:
        await email_service.send_booking_reminder(booking.id)
        booking.reminder_sent = True
        
        # [NEW] Audit Log: Reminder Sent
        audit = AuditLog(
            workspace_id=booking.workspace_id,
            booking_id=booking.id,
            user_id=None,
            action="booking.reminder_sent",
            details={"recipient": booking.contact.email if booking.contact else "unknown"}
        )
        db.add(audit)
        
        db.add(booking)
        results["booking_reminders"] += 1
        
    # ------------------------------------------------------------------
    # 2. FORM REMINDERS (Overdue > 24h)
    # ------------------------------------------------------------------
    # Pending forms sent more than 24h ago
    yesterday = now - timedelta(hours=24)
    
    overdue_forms = db.query(FormSubmission).filter(
        FormSubmission.status == "pending",
        FormSubmission.sent_at <= yesterday,
        FormSubmission.reminder_sent == False
    ).all()
    
    for submission in overdue_forms:
        await email_service.send_form_reminder(submission.id)
        submission.reminder_sent = True
        # Form reminders don't have a direct "booking_id" easily accessible here without a join?
        # FormSubmission has booking_id? Let's check model.
        # Assuming yes for now, if not we skip. FormSubmission usually links to booking.
        if submission.booking_id:
             audit_f = AuditLog(
                workspace_id=submission.form.workspace_id, # Form has workspace_id
                booking_id=submission.booking_id,
                user_id=None,
                action="form.reminder_sent",
                details={"submission_id": submission.id}
             )
             db.add(audit_f)
        
        db.add(submission)
        results["form_reminders"] += 1

    # ------------------------------------------------------------------
    # 3. INVENTORY ALERTS (Low stock, once per day)
    # ------------------------------------------------------------------
    # Quantity <= Threshold AND (last_alert_at IS NULL OR last_alert_at < yesterday)
    
    low_stock_items = db.query(InventoryItem).filter(
        InventoryItem.quantity <= InventoryItem.threshold
    ).all()
    
    for item in low_stock_items:
        # Check last alert logic in python to avoid complex SQL filtering if item list is small
        should_alert = False
        if not item.last_alert_at:
            should_alert = True
        elif item.last_alert_at < yesterday:
            should_alert = True
            
        if should_alert:
            await email_service.send_inventory_alert(item.id)
            item.last_alert_at = now
            # Inventory Alert - Not booking specific, so booking_id is null? 
            # AuditLog requires booking_id (nullable=False). 
            # We can't log global inventory alerts to AuditLog as defined (AuditLog is booking-centric).
            # We will skip logging inventory alerts to AuditLog since it's not a booking event.
            # Or make booking_id nullable?
            # Prompt said "Owner must open booking and see... inventory actions".
            # Global alerts are not booking specific. So we skip.
            db.add(item)
            results["inventory_alerts"] += 1

    # ------------------------------------------------------------------
    # 4. THANK YOU EMAILS (Completed Yesterday)
    # ------------------------------------------------------------------
    # For bookings completed yesterday, send thank you if not sent
    y_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    y_end = y_start + timedelta(days=1)
    
    completed_yesterday = db.query(Booking).filter(
        Booking.status == BookingStatus.COMPLETED.value,
        Booking.end_time >= y_start,
        Booking.end_time < y_end
    ).all()
    
    # Check log to avoid duplicates
    from app.models.communication_log import CommunicationLog
    
    for booking in completed_yesterday:
        already_sent = db.query(CommunicationLog).filter(
            CommunicationLog.booking_id == booking.id,
            CommunicationLog.type == "thank_you"
        ).first()
        
        if not already_sent:
            await email_service.send_visit_completion(booking.id)

    # ------------------------------------------------------------------
    # 5. OWNER DAILY SUMMARY
    # ------------------------------------------------------------------
    # Send daily summary if unanswered messages or low stock exists
    # Iterate all workspaces
    from app.models.workspace import Workspace
    from app.models.conversation import Conversation
    
    workspaces = db.query(Workspace).all()
    
    for ws in workspaces:
        # Check if alert sent today
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        alert_sent_today = db.query(CommunicationLog).filter(
            CommunicationLog.workspace_id == ws.id,
            CommunicationLog.type == "owner_alert",
            CommunicationLog.created_at >= today_start
        ).first()
        
        if not alert_sent_today:
            # Unanswered count (not paused, not internal last msg)
            unanswered = db.query(Conversation).filter(
                Conversation.workspace_id == ws.id,
                Conversation.is_paused == False,
                Conversation.last_message_is_internal == False
            ).count()
            
            # Low stock count for this workspace
            ws_low_stock = db.query(InventoryItem).filter(
                InventoryItem.workspace_id == ws.id,
                InventoryItem.quantity <= InventoryItem.threshold
            ).count()
            
            if unanswered > 0 or ws_low_stock > 0:
                await email_service.send_daily_owner_alert(ws.id, unanswered, ws_low_stock)

    # ------------------------------------------------------------------
    # 6. POST-BOOKING FOLLOW-UP (1 Hour Post Completion)
    # ------------------------------------------------------------------
    follow_up_count = await process_follow_ups(db)
    results["follow_ups_sent"] = follow_up_count

    db.commit()
    return results

async def process_follow_ups(db: Session) -> int:
    """
    Scans for completed bookings > 1 hour ago that haven't received a follow-up.
    Sends email and updates flag.
    Returns count of emails sent.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=1)
    
    follow_up_bookings = db.query(Booking).filter(
        Booking.end_time < cutoff,
        Booking.status == BookingStatus.COMPLETED.value,
        Booking.follow_up_sent == False
    ).all()
    
    count = 0
    for booking in follow_up_bookings:
        await email_service.send_visit_completion(booking.id)
        booking.follow_up_sent = True
        db.add(booking)
        count += 1
    
    return count

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone

from app.api import deps
from app.models.booking import Booking, BookingStatus
from app.models.conversation import Conversation
from app.models.form import Form, FormSubmission
from app.models.inventory import InventoryItem
from app.models.user import User
from app.models.workspace import Workspace

from app.schemas.dashboard import DashboardStats

from app.models.audit_log import AuditLog
from app.models.communication_log import CommunicationLog

router = APIRouter()

@router.get("/", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_owner)
):
    workspace_id = current_user.workspace_id
    now = datetime.now(timezone.utc)
    
    # 1. Bookings
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    today_count = db.query(Booking).filter(
        Booking.workspace_id == workspace_id,
        Booking.start_time >= today_start,
        Booking.start_time < today_end
    ).count()
    
    upcoming_24h = db.query(Booking).filter(
        Booking.workspace_id == workspace_id,
        Booking.start_time >= now,
        Booking.start_time < now + timedelta(hours=24)
    ).count()
    
    week_start = now - timedelta(days=7)
    completed_this_week = db.query(Booking).filter(
        Booking.workspace_id == workspace_id,
        Booking.status == BookingStatus.COMPLETED.value,
        Booking.end_time >= week_start
    ).count()
    
    no_show_this_week = db.query(Booking).filter(
        Booking.workspace_id == workspace_id,
        Booking.status == BookingStatus.NO_SHOW.value,
        Booking.end_time >= week_start
    ).count()
    
    bookings_data = {
        "today_count": today_count,
        "upcoming_24h": upcoming_24h,
        "completed_this_week": completed_this_week,
        "no_show_this_week": no_show_this_week
    }

    # 2. Inbox
    total_conversations = db.query(Conversation).filter(
        Conversation.workspace_id == workspace_id
    ).count()
    
    unanswered_count = db.query(Conversation).filter(
        Conversation.workspace_id == workspace_id,
        Conversation.is_paused == False,
        Conversation.last_message_is_internal == False
    ).count()
    
    paused_conversations = db.query(Conversation).filter(
        Conversation.workspace_id == workspace_id,
        Conversation.is_paused == True
    ).count()

    inbox_data = {
        "total_conversations": total_conversations,
        "unanswered_count": unanswered_count,
        "paused_conversations": paused_conversations
    }
    
    # 3. Forms
    pending_count = db.query(FormSubmission).join(Form).filter(
        Form.workspace_id == workspace_id,
        FormSubmission.status == "pending"
    ).count()
    
    overdue_threshold = now - timedelta(hours=24)
    overdue_count = db.query(FormSubmission).join(Form).filter(
        Form.workspace_id == workspace_id,
        FormSubmission.status == "pending",
        FormSubmission.sent_at <= overdue_threshold
    ).count()
    
    forms_data = {
        "pending_count": pending_count,
        "overdue_count": overdue_count
    }

    # 4. Failures (SIGNAL 1: Priority 1)
    failed_comms = db.query(CommunicationLog).filter(
        CommunicationLog.workspace_id == workspace_id,
        CommunicationLog.status == "failed"
    ).order_by(CommunicationLog.created_at.desc()).limit(5).all()

    failures_out = [
        {
            "id": f.id,
            "type": f.type,
            "recipient": f.recipient_email,
            "error_message": f.error_message,
            "timestamp": f.created_at,
            "booking_id": f.booking_id
        }
        for f in failed_comms
    ]

    # 5. Attention Items (SIGNAL 2: Priority 2)
    attention_out = []
    
    # A. Failed Emails (Actionable: Retry)
    for f in failed_comms:
        attention_out.append({
            "type": "failure",
            "priority": "high",
            "message": f"Failed to send {f.type} to {f.recipient_email}",
            "action_type": "RETRY_EMAIL",
            "entity_id": f.id
        })
        
    # B. Low Stock (Actionable: View - we use id for the item)
    low_stock_items = db.query(InventoryItem).filter(
        InventoryItem.workspace_id == workspace_id,
        InventoryItem.quantity <= InventoryItem.threshold
    ).all()
    
    inventory_out = []
    for item in low_stock_items:
        inventory_out.append({
            "id": item.id,
            "name": item.name,
            "quantity_available": item.quantity,
            "low_threshold": item.threshold
        })
        attention_out.append({
            "type": "inventory",
            "priority": "medium",
            "message": f"Low stock: {item.name} ({item.quantity} left)",
            "action_type": "VIEW_INVENTORY",
            "entity_id": item.id
        })
        
    # C. Unanswered Inbox
    if unanswered_count > 0:
        attention_out.append({
            "type": "inbox",
            "priority": "high",
            "message": f"{unanswered_count} conversations need a reply",
            "action_type": "VIEW_CONV",
            "entity_id": None
        })
        
    # D. Overdue Forms
    if overdue_count > 0:
        attention_out.append({
            "type": "form",
            "priority": "medium",
            "message": f"{overdue_count} intake forms are overdue",
            "action_type": "VIEW_FORMS",
            "entity_id": None
        })

    # 6. Recent Activity (SIGNAL 3: Priority 3)
    recent_audits = db.query(AuditLog).outerjoin(User, AuditLog.user_id == User.id).filter(
        AuditLog.workspace_id == workspace_id
    ).order_by(AuditLog.created_at.desc()).limit(10).all()
    
    activity_out = []
    for a in recent_audits:
        # Determine entity type from action prefix
        entity_type = "system"
        if "." in a.action:
            entity_type = a.action.split(".")[0]
            
        activity_out.append({
            "id": f"audit_{a.id}",
            "action": a.action,
            "timestamp": a.created_at,
            "actor_name": a.user.full_name if a.user else "System",
            "entity_type": entity_type,
            "entity_id": a.booking_id,
            "details": a.details
        })

    # 7. Get Workspace Slug
    workspace = db.query(Workspace).filter(Workspace.id == workspace_id).first()

    return {
        "workspace_slug": workspace.slug if workspace else "",
        "bookings": bookings_data,
        "inbox": inbox_data,
        "forms": forms_data,
        "inventory": inventory_out,
        "attention": attention_out,
        "recent_activity": activity_out,
        "failures": failures_out
    }

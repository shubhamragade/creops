from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone, timedelta

from app.api import deps
from app.schemas.conversation import ConversationOut, MessageOut, MessageCreate
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.models.contact import Contact
from app.services import email as email_service
from app.core.monitoring import log_reply_pause

router = APIRouter()

@router.get("/", response_model=List[ConversationOut])
def get_conversations(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    # List for current workspace
    conversations = db.query(Conversation).filter(
        Conversation.workspace_id == current_user.workspace_id
    ).order_by(Conversation.last_message_at.desc()).all()
    
    # Batch-load contact emails for efficiency
    contact_ids = [c.contact_id for c in conversations if c.contact_id]
    contacts_map = {}
    if contact_ids:
        contacts = db.query(Contact).filter(Contact.id.in_(contact_ids)).all()
        contacts_map = {c.id: c.email for c in contacts}
    
    results = []
    for c in conversations:
        # Logic: Unanswered = Not Paused AND Last Message NOT Internal
        unanswered = (not c.is_paused) and (not c.last_message_is_internal)
        
        c_dict = {
            "id": c.id,
            "subject": c.subject,
            "contact_id": c.contact_id,
            "created_at": c.created_at,
            "updated_at": c.updated_at,
            "is_paused": c.is_paused,
            "paused_until": c.paused_until,
            "last_message_at": c.last_message_at,
            "unanswered": unanswered,
            "contact_email": contacts_map.get(c.contact_id)
        }
        results.append(c_dict)
        
    return results

@router.get("/{conversation_id}", response_model=List[MessageOut])
def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    # Verify access
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.workspace_id == current_user.workspace_id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at.asc()).all()
    
    return messages

@router.post("/messages", response_model=MessageOut)
def send_reply(
    message_in: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_staff_or_owner)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == message_in.conversation_id,
        Conversation.workspace_id == current_user.workspace_id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Create Message
    message = Message(
        conversation_id=conversation.id,
        sender_email=current_user.email,
        content=message_in.content,
        is_internal=True # Staff reply is internal? 
        # Wait, 'is_internal' usually means "Internal Note" vs "Public Reply".
        # But here 'last_message_is_internal' was used for "Staff Reply".
        # Let's assume 'is_internal=True' means "From Staff/System".
        # If the user means "Private Note", that's different.
        # But the brief says "Staff reply -> automation pauses". This implies it's a reply sent to customer.
        # So it's an EXTERNAL message from STAFF.
        # But for 'unanswered' logic: "last message is internal" usually means "we replied".
        # So I will use `is_internal` here to mean "From Staff". 
        # If we need distinguishable "Private Notes", we'd need another flag.
        # Prompt says: "send reply ... send via email ... set conversation.manual_interaction = true".
    )
    db.add(message)
    
    # Update Conversation
    now = datetime.now(timezone.utc)
    conversation.is_paused = True
    conversation.paused_until = now + timedelta(hours=48)
    conversation.last_message_at = now
    conversation.last_message_is_internal = True # We replied
    db.add(conversation)
    
    # [MONITORING] Log pause event
    log_reply_pause(conversation.id, conversation.paused_until)
    
    db.commit()
    db.refresh(message)
    
    # Send Email
    background_tasks.add_task(email_service.send_reply_email, message.id)
    
    return message

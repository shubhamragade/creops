"""
Inbox API - Gmail Sync, Send, and Reply

Uses workspace-isolated Gmail client for all operations.
Auto-creates leads from unknown senders.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, EmailStr
import base64
from email.mime.text import MIMEText
from email.utils import parseaddr
from datetime import datetime, timedelta, timezone

from app.api import deps
from app.services.gmail_client import get_gmail_client
from app.models.contact import Contact
from app.models.conversation import Conversation, Message

router = APIRouter()


# Schemas
class EmailThread(BaseModel):
    id: str
    subject: str
    sender_email: str
    sender_name: Optional[str] = None
    date: str
    is_unread: bool
    message_count: int


class EmailMessage(BaseModel):
    id: str
    sender: str
    subject: str
    date: str
    body: str


class ThreadDetail(BaseModel):
    thread_id: str
    messages: List[EmailMessage]


class SendEmailRequest(BaseModel):
    to_email: EmailStr
    subject: str
    body: str


class ReplyEmailRequest(BaseModel):
    thread_id: str
    body: str


@router.post("/inbox/sync")
def sync_inbox_from_gmail(
    background_tasks: BackgroundTasks,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Sync email threads from Gmail and save to database.
    POST method for action.
    """
    try:
        # Get workspace-specific Gmail client
        service = get_gmail_client(current_user.workspace_id, db)
        
        # Fetch threads
        results = service.users().threads().list(
            userId='me',
            maxResults=20, 
            labelIds=['INBOX']
        ).execute()
        
        threads = results.get('threads', [])
        synced_count = 0
        
        for thread in threads:
            thread_id = thread['id']
            
            # Get full thread details
            thread_data = service.users().threads().get(
                userId='me',
                id=thread_id,
                format='full' 
            ).execute()
            
            messages = thread_data.get('messages', [])
            if not messages: continue

            # Sort by date
            messages.sort(key=lambda x: int(x['internalDate']))
            
            # 1. Identify Contact & Conversation
            first_msg = messages[0]
            headers = {h['name']: h['value'] for h in first_msg.get('payload', {}).get('headers', [])}
            subject = headers.get('Subject', 'No Subject')
            
            # Find contact from ANY message in thread? 
            # Usually the first message determines the thread starter.
            # But if WE started the thread, the contact is the TO field.
            # If THEY started, contact is FROM.
            # Simplified Logic: Check current DB conversations for this thread_id? 
            # We haven't been storing thread_id in Conversation model. 
            # We match by Contact Email for now.
            
            # Extract distinct emails in thread to find the contact
            thread_emails = set()
            for msg in messages:
                h = {k['name']: k['value'] for k in msg.get('payload', {}).get('headers', [])}
                sender = parseaddr(h.get('From', ''))[1]
                recip = parseaddr(h.get('To', ''))[1]
                if sender: thread_emails.add(sender)
                if recip: thread_emails.add(recip)

            # Find valid contact among these emails
            contact = db.query(Contact).filter(
                Contact.email.in_(thread_emails),
                Contact.workspace_id == current_user.workspace_id
            ).first()
            
            if not contact:
                # Try to create from the FROM of first message if it is not us?
                # Assume "We" are the workspace.google_email (if we knew it easily here).
                # Fallback: Just take the first non-me email? 
                # For now, simplistic approach: From header of first message
                f_from = parseaddr(headers.get('From', ''))[1]
                # If valid email and not our user (simplified)
                contact = Contact(
                    workspace_id=current_user.workspace_id,
                    email=f_from,
                    first_name="New",
                    last_name="Lead",
                    status="new",
                    source="email"
                )
                db.add(contact)
                db.commit()
                db.refresh(contact)

            # Find or Create Conversation
            # ideally we match by thread_id if we stored it. 
            # For now, we match by Contact + Subject match? Or just latest conversation?
            # Let's Find the latest conversation with this contact.
            conversation = db.query(Conversation).filter(
                Conversation.contact_id == contact.id,
                Conversation.workspace_id == current_user.workspace_id
            ).order_by(Conversation.created_at.desc()).first()
            
            # Check subject match or recency ( < 2 days?)
            # Or just ALWAYS create new if not found?
            if not conversation:
                conversation = Conversation(
                    workspace_id=current_user.workspace_id,
                    contact_id=contact.id,
                    subject=subject,
                    created_at=datetime.now(timezone.utc),
                    last_message_at=datetime.now(timezone.utc),
                    is_paused=False
                )
                db.add(conversation)
                db.commit()
                db.refresh(conversation)
            
            # 2. Sync Messages
            # We need to avoid duplicates. Check existing Message IDs? 
            # We don't store Gmail ID in Message table currently... 
            # We store content. 
            # Let's add specific logic: Check if message content + timestamp exists?
            # Better: We can't easily dedup without Gmail ID.
            # SKIP for now: We will just insert NEW messages based on timestamp?
            # This is risky. 
            # HACK: Just insert IF content doesn't exist for this conversation.
            
            existing_contents = set(
                db.query(Message.content).filter(Message.conversation_id == conversation.id).all()
            )
            existing_contents = {r[0] for r in existing_contents} # Set of strings

            updates_made = False
            for msg in messages:
                # Extract Body
                body = ""
                payload = msg.get('payload', {})
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part.get('mimeType') == 'text/plain':
                            d = part.get('body', {}).get('data', '')
                            if d: body = base64.urlsafe_b64decode(d).decode(errors='ignore')
                else:
                    d = payload.get('body', {}).get('data', '')
                    if d: body = base64.urlsafe_b64decode(d).decode(errors='ignore')
                
                if not body: continue
                
                # Check duplication (Simple content check)
                if body in existing_contents:
                    continue

                # Determine direction
                msg_headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
                sender_email = parseaddr(msg_headers.get('From', ''))[1]
                
                # Is Internal? (If sender is workspace owner/staff)
                # We can check if sender_email matches a User in this workspace
                # OR is the connected gmail address.
                # Simplification: If sender == contact.email, it is EXTERNAL (False). Else Internal.
                is_internal = (sender_email != contact.email)

                new_msg = Message(
                    conversation_id=conversation.id,
                    sender_email=sender_email,
                    content=body,
                    is_internal=is_internal,
                    created_at=datetime.fromtimestamp(int(msg['internalDate'])/1000, tz=timezone.utc)
                )
                db.add(new_msg)
                existing_contents.add(body)
                synced_count += 1
                updates_made = True
                
                # Update Conversation Last Message
                if new_msg.created_at > conversation.last_message_at.replace(tzinfo=timezone.utc):
                    conversation.last_message_at = new_msg.created_at
                    conversation.last_message_is_internal = is_internal
                    
                    # If External, Unpause?
                    if not is_internal:
                        conversation.is_paused = False

            if updates_made:
                db.commit()

        return {"status": "success", "synced_messages": synced_count}
    
    except Exception as e:
        print(f"Sync Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/inbox/threads/{thread_id}", response_model=ThreadDetail)
def get_thread_details(
    thread_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Get all messages in a thread.
    """
    try:
        service = get_gmail_client(current_user.workspace_id, db)
        
        # Get thread with full message content
        thread_data = service.users().threads().get(
            userId='me',
            id=thread_id,
            format='full'
        ).execute()
        
        messages = []
        for msg in thread_data.get('messages', []):
            headers = {h['name']: h['value'] for h in msg.get('payload', {}).get('headers', [])}
            
            # Extract body
            body = ""
            payload = msg.get('payload', {})
            
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        body_data = part.get('body', {}).get('data', '')
                        if body_data:
                            body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
                            break
            else:
                body_data = payload.get('body', {}).get('data', '')
                if body_data:
                    body = base64.urlsafe_b64decode(body_data).decode('utf-8', errors='ignore')
            
            messages.append(EmailMessage(
                id=msg['id'],
                sender=headers.get('From', ''),
                subject=headers.get('Subject', ''),
                date=headers.get('Date', ''),
                body=body[:2000]  # Limit body length
            ))
        
        return ThreadDetail(
            thread_id=thread_id,
            messages=messages
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch thread: {str(e)}")


@router.post("/inbox/send")
def send_email(
    request: SendEmailRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Send email from workspace Gmail account.
    """
    try:
        service = get_gmail_client(current_user.workspace_id, db)
        
        # Create message
        message = MIMEText(request.body)
        message['to'] = request.to_email
        message['subject'] = request.subject
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send
        service.users().messages().send(
            userId='me',
            body={'raw': raw_message}
        ).execute()
        
        return {
            "message": "Email sent successfully",
            "to": request.to_email
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/inbox/reply")
def reply_to_email(
    request: ReplyEmailRequest,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Reply to an email thread.
    """
    try:
        service = get_gmail_client(current_user.workspace_id, db)
        
        # Get thread to extract recipient
        thread_data = service.users().threads().get(
            userId='me',
            id=request.thread_id,
            format='metadata',
            metadataHeaders=['From', 'Subject']
        ).execute()
        
        messages = thread_data.get('messages', [])
        if not messages:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        first_msg = messages[0]
        headers = {h['name']: h['value'] for h in first_msg.get('payload', {}).get('headers', [])}
        
        to_email = parseaddr(headers.get('From', ''))[1]
        subject = headers.get('Subject', '')
        
        # Add Re: if not present
        if not subject.startswith('Re:'):
            subject = f"Re: {subject}"
        
        # Create reply message
        message = MIMEText(request.body)
        message['to'] = to_email
        message['subject'] = subject
        message['In-Reply-To'] = first_msg['id']
        message['References'] = first_msg['id']
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send reply
        service.users().messages().send(
            userId='me',
            body={
                'raw': raw_message,
                'threadId': request.thread_id
            }
        ).execute()
        
        # Pause automations for matching conversation (hackathon brief: "Staff reply → automation stops")
        from app.models.conversation import Conversation
        from app.models.contact import Contact
        contact = db.query(Contact).filter(
            Contact.email == to_email,
            Contact.workspace_id == current_user.workspace_id
        ).first()
        if contact:
            conv = db.query(Conversation).filter(
                Conversation.contact_id == contact.id,
                Conversation.workspace_id == current_user.workspace_id
            ).first()
            if conv:
                conv.is_paused = True
                conv.paused_until = datetime.utcnow() + timedelta(hours=48)
                conv.last_message_is_internal = True
                db.commit()
        
        return {
            "message": "Reply sent successfully",
            "thread_id": request.thread_id
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send reply: {str(e)}")

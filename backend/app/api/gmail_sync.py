from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
import base64
from email.utils import parseaddr
from datetime import datetime

from app.api import deps
from app.models.workspace import Workspace
from app.models.contact import Contact
from app.models.conversation import Conversation
from app.core.security_utils import decrypt_token
from app.core.config import settings

router = APIRouter()

from app.services.gmail_client import GmailClientService

@router.get("/inbox/threads")
def get_inbox_threads(
    max_results: int = 50,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Fetch email threads from Gmail
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == current_user.workspace_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    try:
        service = GmailClientService.get_gmail_client(workspace.id, db)
        
        # Get threads from inbox
        results = service.users().threads().list(
            userId='me',
            maxResults=max_results,
            labelIds=['INBOX']
        ).execute()
        
        threads = results.get('threads', [])
        
        thread_list = []
        for thread in threads[:20]:  # Limit to 20 for hackathon
            thread_id = thread['id']
            
            # Get thread details
            thread_data = service.users().threads().get(
                userId='me',
                id=thread_id,
                format='metadata',
                metadataHeaders=['From', 'Subject', 'Date']
            ).execute()
            
            messages = thread_data.get('messages', [])
            if not messages:
                continue
            
            # Get first message for subject and sender
            first_msg = messages[0]
            headers = {h['name']: h['value'] for h in first_msg.get('payload', {}).get('headers', [])}
            
            sender_email = parseaddr(headers.get('From', ''))[1]
            subject = headers.get('Subject', 'No Subject')
            date = headers.get('Date', '')
            
            # Check if unread
            is_unread = 'UNREAD' in first_msg.get('labelIds', [])
            
            thread_list.append({
                'id': thread_id,
                'subject': subject,
                'sender_email': sender_email,
                'date': date,
                'is_unread': is_unread,
                'message_count': len(messages)
            })
        
        return thread_list
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")

@router.get("/inbox/thread/{thread_id}")
def get_thread_messages(
    thread_id: str,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user)
):
    """
    Get all messages in a thread
    """
    workspace = db.query(Workspace).filter(
        Workspace.id == current_user.workspace_id
    ).first()
    
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    
    try:
        service = GmailClientService.get_gmail_client(workspace.id, db)
        
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
            
            messages.append({
                'id': msg['id'],
                'sender': headers.get('From', ''),
                'subject': headers.get('Subject', ''),
                'date': headers.get('Date', ''),
                'body': body[:1000]  # Limit body length
            })
        
        # Auto-create lead if sender unknown
        if messages:
            first_msg = messages[0]
            sender_email = parseaddr(first_msg['sender'])[1]
            
            # Check if contact exists
            contact = db.query(Contact).filter(
                Contact.email == sender_email,
                Contact.workspace_id == workspace.id
            ).first()
            
            if not contact:
                # Create new lead
                contact = Contact(
                    email=sender_email,
                    workspace_id=workspace.id,
                    status='new',
                    source='email'
                )
                db.add(contact)
                db.commit()
        
        return {
            'thread_id': thread_id,
            'messages': messages
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch thread: {str(e)}")

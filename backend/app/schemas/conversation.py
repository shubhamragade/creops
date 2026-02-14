from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class MessageCreate(BaseModel):
    conversation_id: int
    content: str

class MessageOut(BaseModel):
    id: int
    conversation_id: int
    sender_email: str
    content: str
    is_internal: bool
    created_at: datetime

    class Config:
        orm_mode = True

class ConversationOut(BaseModel):
    id: int
    subject: Optional[str]
    contact_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_paused: bool
    paused_until: Optional[datetime]
    last_message_at: Optional[datetime]
    unanswered: bool # Computed field
    contact_email: Optional[str] = None

    class Config:
        orm_mode = True

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class AuditLogBase(BaseModel):
    action: str
    details: Optional[Dict[str, Any]] = None

class AuditLogOut(AuditLogBase):
    id: int
    booking_id: int
    user_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

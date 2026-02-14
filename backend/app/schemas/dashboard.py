from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ActivityItem(BaseModel):
    id: str # audit_{id}
    action: str
    timestamp: datetime
    actor_name: Optional[str] = None
    entity_type: str # booking, inventory, etc.
    entity_id: Optional[int] = None
    details: Optional[dict] = None

class FailureItem(BaseModel):
    id: int # communication_log_id
    type: str
    recipient: str
    error_message: Optional[str] = None
    timestamp: datetime
    booking_id: Optional[int] = None

class AttentionItem(BaseModel):
    type: str # failure, inventory, inbox, form
    priority: str # high, medium, low
    message: str
    action_type: str # RETRY_EMAIL, VIEW_BOOKING, VIEW_CONV, VIEW_SUBMISSION
    entity_id: Optional[int] = None

class InventoryItemOut(BaseModel):
    id: int
    name: str
    quantity_available: int
    low_threshold: int

class DashboardStats(BaseModel):
    workspace_slug: str
    bookings: dict
    inbox: dict
    forms: dict
    inventory: List[InventoryItemOut]
    attention: List[AttentionItem]
    recent_activity: List[ActivityItem]
    failures: List[FailureItem]

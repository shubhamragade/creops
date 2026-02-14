from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)  # Nullable for non-booking events
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True) # Null for system actions
    
    action = Column(String, nullable=False) # e.g. "booking.created", "status.change"
    details = Column(JSON, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    workspace = relationship("Workspace")
    booking = relationship("Booking")
    user = relationship("User")

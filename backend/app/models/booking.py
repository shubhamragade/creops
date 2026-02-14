from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum

class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String, default=BookingStatus.PENDING.value)
    reminder_sent = Column(Boolean, default=False)
    follow_up_sent = Column(Boolean, default=False) # For post-visit automation
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    service_id = Column(Integer, ForeignKey("services.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"))
    staff_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    workspace = relationship("Workspace", back_populates="bookings")
    service = relationship("Service", back_populates="bookings")
    contact = relationship("Contact", back_populates="bookings")
    staff_member = relationship("User", back_populates="bookings")

    form_submissions = relationship("FormSubmission", back_populates="booking")


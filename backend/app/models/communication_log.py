from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class CommunicationLog(Base):
    __tablename__ = "communication_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True)
    
    type = Column(String, nullable=False) # welcome, confirmation, form_link, reminder, reply, inventory
    recipient_email = Column(String, nullable=False)
    status = Column(String, default="pending") # success, failed
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    sent_at = Column(DateTime(timezone=True), nullable=True)  # When email was actually delivered

    # Relationships (optional for now, but good for navigation)
    workspace = relationship("Workspace")
    contact = relationship("Contact")
    booking = relationship("Booking")

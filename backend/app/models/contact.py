from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=False)
    phone = Column(String)
    full_name = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    
    # Lead management fields
    status = Column(String, default="new")  # new, contacted, booked
    source = Column(String, default="manual")  # form, booking, manual
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    workspace = relationship("Workspace", back_populates="contacts")
    bookings = relationship("Booking", back_populates="contact")
    conversations = relationship("Conversation", back_populates="contact")

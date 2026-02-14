from sqlalchemy import Column, Integer, String, ForeignKey, JSON, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Form(Base):
    __tablename__ = "forms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(String) # contact, booking, intake
    is_public = Column(Boolean, default=True)
    fields = Column(JSON, default=[]) 
    google_form_url = Column(String, nullable=True)  # Optional Google Form URL
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    
    workspace = relationship("Workspace", back_populates="forms")
    submissions = relationship("FormSubmission", back_populates="form")

class FormSubmission(Base):
    __tablename__ = "form_submissions"

    id = Column(Integer, primary_key=True, index=True)
    form_id = Column(Integer, ForeignKey("forms.id"))
    booking_id = Column(Integer, ForeignKey("bookings.id"), nullable=True) # Optional link
    status = Column(String, default="pending") # pending, completed
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    reminder_sent = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    data = Column(JSON, nullable=True)
    
    form = relationship("Form", back_populates="submissions")
    booking = relationship("Booking", back_populates="form_submissions")

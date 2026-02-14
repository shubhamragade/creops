from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy.sql import func
from app.db.base_class import Base

class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    address = Column(String)
    timezone = Column(String, default="Asia/Kolkata")
    contact_email = Column(String)
    email_config = Column(JSON, default={})  # Stores API keys/provider/from_email
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    users = relationship("User", back_populates="workspace")
    services = relationship("Service", back_populates="workspace")
    contacts = relationship("Contact", back_populates="workspace")
    forms = relationship("Form", back_populates="workspace", lazy="dynamic")
    inventory_items = relationship("InventoryItem", back_populates="workspace")

    bookings = relationship("Booking", back_populates="workspace")
    
    # Email integration (new multi-tenant approach)
    email_integration = relationship("EmailIntegration", back_populates="workspace", uselist=False)

    # Google Gmail API Integration (DEPRECATED - will be removed after migration)
    google_connected = Column(Boolean, default=False)
    google_refresh_token = Column(String) # Encrypted
    google_email = Column(String)
    google_token_expiry = Column(DateTime)
    google_from_name = Column(String)

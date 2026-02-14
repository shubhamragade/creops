from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    availability = Column(JSON, default={}) # e.g. {"mon": ["09:00-17:00"]}
    location = Column(String)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    inventory_item_id = Column(Integer, ForeignKey("inventory_items.id"), nullable=True)
    inventory_quantity_required = Column(Integer, default=0) # e.g. 1 unit per booking
    
    workspace = relationship("Workspace", back_populates="services")
    inventory_item = relationship("InventoryItem") # No back_populates needed yet
    bookings = relationship("Booking", back_populates="service")

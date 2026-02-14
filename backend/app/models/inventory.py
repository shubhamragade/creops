from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class InventoryItem(Base):
    __tablename__ = "inventory_items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    quantity = Column(Integer, default=0)
    threshold = Column(Integer, default=5)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    last_alert_at = Column(DateTime(timezone=True), nullable=True)

    workspace = relationship("Workspace", back_populates="inventory_items")

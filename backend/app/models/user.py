from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.orm import relationship
from app.db.base_class import Base
import enum

class UserRole(str, enum.Enum):
    OWNER = "owner"
    STAFF = "staff"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(String, default=UserRole.STAFF.value)
    is_active = Column(Boolean, default=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    permissions = Column(String, default="{}") # Simple JSON string or JSON type

    workspace = relationship("Workspace", back_populates="users")
    bookings = relationship("Booking", back_populates="staff_member", foreign_keys="Booking.staff_id")





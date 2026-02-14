from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base


class EmailIntegration(Base):
    """
    Email integration for workspaces.
    Each workspace can connect one email provider (Google, Microsoft, etc.)
    Tokens are encrypted at rest for security.
    """
    __tablename__ = "email_integrations"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(50), nullable=False, default="google")
    email = Column(String(255), nullable=False)
    
    # Encrypted tokens
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    scope = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    
    connected_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    workspace = relationship("Workspace", back_populates="email_integration")

    # Constraints
    __table_args__ = (
        UniqueConstraint('workspace_id', 'provider', name='uq_workspace_provider'),
        {'extend_existing': True}
    )

    def __repr__(self):
        return f"<EmailIntegration(id={self.id}, workspace_id={self.workspace_id}, email={self.email}, provider={self.provider})>"

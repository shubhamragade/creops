"""create_email_integrations_table

Revision ID: 172a0f5be972
Revises: 
Create Date: 2026-02-13

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '172a0f5be972'
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'email_integrations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False, server_default='google'),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_sync_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('connected_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('workspace_id', 'provider', name='uq_workspace_provider')
    )
    
    # Create indexes
    op.create_index('idx_email_integrations_workspace_provider', 'email_integrations', ['workspace_id', 'provider'])
    op.create_index('idx_email_integrations_active', 'email_integrations', ['is_active'])


def downgrade():
    op.drop_index('idx_email_integrations_active', table_name='email_integrations')
    op.drop_index('idx_email_integrations_workspace_provider', table_name='email_integrations')
    op.drop_table('email_integrations')

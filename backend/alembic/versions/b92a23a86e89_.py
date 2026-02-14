"""empty message

Revision ID: b92a23a86e89
Revises: 172a0f5be972, 80cb8684db91
Create Date: 2026-02-13 14:11:55.862800

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b92a23a86e89'
down_revision: Union[str, Sequence[str], None] = ('172a0f5be972', '80cb8684db91')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

"""merge certificado electronico con migraciones actuales

Revision ID: 6efc698b6ae0
Revises: 42870faf9274, f2a9c6d4e8b1
Create Date: 2026-09-14 20:09:44.113098

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6efc698b6ae0'
down_revision: Union[str, Sequence[str], None] = ('42870faf9274', 'f2a9c6d4e8b1')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass

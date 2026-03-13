"""unificando migracoes

Revision ID: 527ce72735e0
Revises: f1e94d82ca82
Create Date: 2026-03-13 13:20:34.716519

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '527ce72735e0'
down_revision: Union[str, None] = 'f1e94d82ca82'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

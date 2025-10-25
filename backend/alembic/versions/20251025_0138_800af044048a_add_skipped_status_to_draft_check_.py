"""Add skipped status to draft check constraint

Revision ID: 800af044048a
Revises: b9cc074b4076
Create Date: 2025-10-25 01:38:42.315193+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '800af044048a'
down_revision: Union[str, None] = 'b9cc074b4076'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the old check constraint
    op.drop_constraint('drafts_status_check', 'drafts', type_='check')

    # Create new check constraint with 'skipped' status
    op.create_check_constraint(
        'drafts_status_check',
        'drafts',
        "status IN ('pending', 'approved', 'rejected', 'sent', 'edited', 'skipped')"
    )


def downgrade() -> None:
    # Drop the new check constraint
    op.drop_constraint('drafts_status_check', 'drafts', type_='check')

    # Restore old check constraint without 'skipped'
    op.create_check_constraint(
        'drafts_status_check',
        'drafts',
        "status IN ('pending', 'approved', 'rejected', 'sent', 'edited')"
    )

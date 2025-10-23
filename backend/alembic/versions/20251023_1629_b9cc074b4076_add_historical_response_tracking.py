"""add_historical_response_tracking

Revision ID: b9cc074b4076
Revises: c6accb3b838c
Create Date: 2025-10-23 16:29:20.940800+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'b9cc074b4076'
down_revision: Union[str, None] = 'c6accb3b838c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create historical_response_examples table
    op.create_table(
        'historical_response_examples',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inquiry_lead_id', sa.Integer(), nullable=True),
        sa.Column('inquiry_subject', sa.Text(), nullable=True),
        sa.Column('inquiry_body', sa.Text(), nullable=True),
        sa.Column('inquiry_sender_email', sa.String(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=False),
        sa.Column('response_subject', sa.String(), nullable=True),
        sa.Column('response_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('metadata', postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['inquiry_lead_id'], ['leads.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_historical_response_examples_id'), 'historical_response_examples', ['id'], unique=False)
    op.create_index(op.f('ix_historical_response_examples_inquiry_lead_id'), 'historical_response_examples', ['inquiry_lead_id'], unique=False)
    op.create_index(op.f('ix_historical_response_examples_is_active'), 'historical_response_examples', ['is_active'], unique=False)

    # Add columns to leads table
    op.add_column('leads', sa.Column('is_historical', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('leads', sa.Column('source_type', sa.String(), nullable=True, server_default='current'))
    op.add_column('leads', sa.Column('human_response_body', sa.Text(), nullable=True))
    op.add_column('leads', sa.Column('human_response_date', sa.TIMESTAMP(timezone=True), nullable=True))

    # Create indexes for new columns
    op.create_index(op.f('ix_leads_is_historical'), 'leads', ['is_historical'], unique=False)
    op.create_index(op.f('ix_leads_source_type'), 'leads', ['source_type'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_leads_source_type'), table_name='leads')
    op.drop_index(op.f('ix_leads_is_historical'), table_name='leads')

    # Drop columns from leads table
    op.drop_column('leads', 'human_response_date')
    op.drop_column('leads', 'human_response_body')
    op.drop_column('leads', 'source_type')
    op.drop_column('leads', 'is_historical')

    # Drop historical_response_examples table
    op.drop_index(op.f('ix_historical_response_examples_is_active'), table_name='historical_response_examples')
    op.drop_index(op.f('ix_historical_response_examples_inquiry_lead_id'), table_name='historical_response_examples')
    op.drop_index(op.f('ix_historical_response_examples_id'), table_name='historical_response_examples')
    op.drop_table('historical_response_examples')

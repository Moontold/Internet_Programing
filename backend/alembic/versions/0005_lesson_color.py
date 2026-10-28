"""lesson and series color

Revision ID: 0005
Revises: 0004
Create Date: 2026-10-28
"""
from alembic import op
import sqlalchemy as sa


revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # null — без цвета: занятие берёт цвет серии, серия — цвет календаря по умолчанию
    op.add_column('lesson_series', sa.Column('color', sa.String(length=7), nullable=True))
    op.add_column('lessons', sa.Column('color', sa.String(length=7), nullable=True))


def downgrade() -> None:
    op.drop_column('lessons', 'color')
    op.drop_column('lesson_series', 'color')

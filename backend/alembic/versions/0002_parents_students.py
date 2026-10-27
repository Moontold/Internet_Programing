"""parents and students

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa


revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'parents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('phone', sa.String(length=32), nullable=False),
        sa.Column('contacts_note', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_table(
        'students',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('parent_id', sa.Integer(), nullable=False),
        sa.Column('grade', sa.Integer(), nullable=True),
        sa.Column('grade_note', sa.String(length=100), nullable=False),
        sa.Column('format', sa.String(length=16), nullable=False),
        sa.Column('price_per_lesson', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['parent_id'], ['parents.id']),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_students_parent_id'), 'students', ['parent_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_students_parent_id'), table_name='students')
    op.drop_table('students')
    op.drop_table('parents')

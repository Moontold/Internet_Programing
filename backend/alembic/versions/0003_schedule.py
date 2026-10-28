"""lesson series and lessons

Revision ID: 0003
Revises: 0002
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa


revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'lesson_series',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('first_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('interval_weeks', sa.Integer(), nullable=False),
        sa.Column('until', sa.Date(), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'series_students',
        sa.Column('series_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['series_id'], ['lesson_series.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('series_id', 'student_id'),
    )
    op.create_table(
        'lessons',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('series_id', sa.Integer(), nullable=True),
        sa.Column('original_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('detached', sa.Boolean(), nullable=False),
        sa.Column('topic', sa.String(length=300), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['series_id'], ['lesson_series.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('series_id', 'original_start', name='uq_lesson_series_original'),
    )
    op.create_index(op.f('ix_lessons_scheduled_start'), 'lessons', ['scheduled_start'], unique=False)
    op.create_index(op.f('ix_lessons_series_id'), 'lessons', ['series_id'], unique=False)
    op.create_index(op.f('ix_lessons_status'), 'lessons', ['status'], unique=False)
    op.create_table(
        'lesson_students',
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('lesson_id', 'student_id'),
    )


def downgrade() -> None:
    op.drop_table('lesson_students')
    op.drop_index(op.f('ix_lessons_status'), table_name='lessons')
    op.drop_index(op.f('ix_lessons_series_id'), table_name='lessons')
    op.drop_index(op.f('ix_lessons_scheduled_start'), table_name='lessons')
    op.drop_table('lessons')
    op.drop_table('series_students')
    op.drop_table('lesson_series')

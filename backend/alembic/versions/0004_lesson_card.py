"""lesson card: homework, notes, grades, files

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-07
"""
from alembic import op
import sqlalchemy as sa


revision = '0004'
down_revision = '0003'
branch_labels = None
depends_on = None

LESSON_TEXT_COLUMNS = ('homework_text', 'parent_comment', 'tutor_notes')


def upgrade() -> None:
    # Пустая строка по умолчанию нужна только чтобы заполнить уже существующие занятия
    for column in LESSON_TEXT_COLUMNS:
        op.add_column('lessons', sa.Column(column, sa.Text(), nullable=False, server_default=''))
        op.alter_column('lessons', column, server_default=None)
    op.add_column('lessons', sa.Column('homework_saved_at', sa.DateTime(timezone=True), nullable=True))

    op.add_column(
        'lesson_students',
        sa.Column('homework_status', sa.String(length=16), nullable=False, server_default='not_checked'),
    )
    op.alter_column('lesson_students', 'homework_status', server_default=None)
    op.add_column('lesson_students', sa.Column('homework_grade', sa.Integer(), nullable=True))

    op.create_table(
        'files',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('original_name', sa.String(length=255), nullable=False),
        sa.Column('stored_name', sa.String(length=64), nullable=False),
        sa.Column('size', sa.BigInteger(), nullable=False),
        sa.Column('mime', sa.String(length=100), nullable=False),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stored_name'),
    )
    op.create_table(
        'lesson_files',
        sa.Column('lesson_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['file_id'], ['files.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('lesson_id', 'file_id'),
    )


def downgrade() -> None:
    op.drop_table('lesson_files')
    op.drop_table('files')
    op.drop_column('lesson_students', 'homework_grade')
    op.drop_column('lesson_students', 'homework_status')
    op.drop_column('lessons', 'homework_saved_at')
    for column in reversed(LESSON_TEXT_COLUMNS):
        op.drop_column('lessons', column)

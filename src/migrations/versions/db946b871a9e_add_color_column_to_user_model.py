"""Add color column to User model

Revision ID: db946b871a9e
Revises: 649182449e0e
Create Date: 2025-02-27 20:43:00.374193

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'db946b871a9e'
down_revision = '649182449e0e'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Add the column with a default value to prevent NULL constraint issues.
    op.add_column('users', sa.Column('color', sa.String(length=7), nullable=True, server_default='#3498db'))

    # Step 2: Manually update existing users to set their color to the default.
    op.execute("UPDATE users SET color = '#3498db' WHERE color IS NULL")

    # Step 3: Alter the column to enforce NOT NULL after updating all rows.
    op.alter_column('users', 'color', nullable=False)

def downgrade():
    op.drop_column('users', 'color')

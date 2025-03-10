"""Add due_days column and chore assignment features

Revision ID: 649182449e0e
Revises: d7d9b7cec4e3
Create Date: 2025-02-27 20:12:37.489197

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '649182449e0e'
down_revision = 'd7d9b7cec4e3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('chore_assignees',
    sa.Column('chore_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['chore_id'], ['chores.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('chore_id', 'user_id')
    )
    op.create_table('chore_completions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chore_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['chore_id'], ['chores.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('chore_completions')
    op.drop_table('chore_assignees')
    # ### end Alembic commands ###

"""allow student users

Revision ID: 2a6cce463bac
Revises: 04cbaa599733
Create Date: 2023-06-13 13:53:43.396011

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2a6cce463bac"
down_revision = "04cbaa599733"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("course", schema=None) as batch_op:
        batch_op.add_column(sa.Column("student_allowed", sa.BOOLEAN(), nullable=True))

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_student", sa.BOOLEAN(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("is_student")

    with op.batch_alter_table("course", schema=None) as batch_op:
        batch_op.drop_column("student_allowed")

    # ### end Alembic commands ###
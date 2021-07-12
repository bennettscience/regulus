"""go back to association only

Revision ID: 3423705349bc
Revises: 41bbdc2cba04
Create Date: 2021-05-26 11:58:05.449457

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '3423705349bc'
down_revision = '41bbdc2cba04'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('attended')
    with op.batch_alter_table('course_attendees', schema=None) as batch_op:
        batch_op.add_column(sa.Column('attended', sa.Boolean(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('course_attendees', schema=None) as batch_op:
        batch_op.drop_column('attended')

    op.create_table('attended',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('course_id', sa.INTEGER(), nullable=False),
    sa.Column('attended', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['course.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'course_id')
    )
    # ### end Alembic commands ###

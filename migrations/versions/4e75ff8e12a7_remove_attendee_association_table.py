"""remove attendee association table

Revision ID: 4e75ff8e12a7
Revises: a6b7e648a9de
Create Date: 2021-05-28 08:36:07.154675

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4e75ff8e12a7'
down_revision = 'a6b7e648a9de'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('course_user_attended',
    sa.Column('course_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('attended', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['course.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('course_id', 'user_id')
    )
    op.drop_table('course_attendees')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('course_attendees',
    sa.Column('user_id', sa.INTEGER(), nullable=False),
    sa.Column('course_id', sa.INTEGER(), nullable=False),
    sa.Column('attended', sa.BOOLEAN(), nullable=True),
    sa.ForeignKeyConstraint(['course_id'], ['course.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'course_id')
    )
    op.drop_table('course_user_attended')
    # ### end Alembic commands ###

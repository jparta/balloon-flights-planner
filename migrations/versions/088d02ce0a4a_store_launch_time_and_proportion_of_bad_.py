"""Store launch time and proportion of bad area

Revision ID: 088d02ce0a4a
Revises: 3df251028051
Create Date: 2023-07-20 15:53:56.873857

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '088d02ce0a4a'
down_revision = '3df251028051'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('trajectory_prediction_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('launch_time', sa.DateTime(), nullable=False))
        batch_op.add_column(sa.Column('bad_landing_proportion', sa.Float(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('trajectory_prediction_data', schema=None) as batch_op:
        batch_op.drop_column('bad_landing_proportion')
        batch_op.drop_column('launch_time')

    # ### end Alembic commands ###

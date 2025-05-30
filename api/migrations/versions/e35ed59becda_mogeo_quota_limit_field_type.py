"""mogeo quota limit field type

Revision ID: e35ed59becda
Revises: 16fa53d9faec
Create Date: 2023-08-09 22:20:31.577953

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e35ed59becda'
down_revision = '16fa53d9faec'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('providers', schema=None) as batch_op:
        batch_op.alter_column('quota_limit',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               existing_nullable=True)
        batch_op.alter_column('quota_used',
               existing_type=sa.INTEGER(),
               type_=sa.BigInteger(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('providers', schema=None) as batch_op:
        batch_op.alter_column('quota_used',
               existing_type=sa.BigInteger(),
               type_=sa.INTEGER(),
               existing_nullable=True)
        batch_op.alter_column('quota_limit',
               existing_type=sa.BigInteger(),
               type_=sa.INTEGER(),
               existing_nullable=True)

    # ### end Alembic commands ###

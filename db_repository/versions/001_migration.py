from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
GIP_opportunities = Table('GIP_opportunities', pre_meta,
    Column('tn_code', VARCHAR(length=20), primary_key=True, nullable=False),
    Column('country', VARCHAR(length=30)),
    Column('segment_id', VARCHAR(length=40)),
)

GIP__e_ps = Table('GIP__e_ps', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('tn_code', VARCHAR(length=20)),
    Column('user_id', VARCHAR(length=120)),
    Column('departure_time', INTEGER),
    Column('return_time', INTEGER),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['GIP_opportunities'].drop()
    pre_meta.tables['GIP__e_ps'].columns['tn_code'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['GIP_opportunities'].create()
    pre_meta.tables['GIP__e_ps'].columns['tn_code'].create()

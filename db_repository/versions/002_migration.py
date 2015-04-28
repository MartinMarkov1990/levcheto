from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
GIP__e_ps = Table('GIP__e_ps', post_meta,
    Column('id', Integer, primary_key=True, nullable=False),
    Column('user_id', String(length=120)),
    Column('country_name', String(length=30)),
    Column('segment_id', String(length=40)),
    Column('departure_time', Integer),
    Column('return_time', Integer),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['GIP__e_ps'].columns['country_name'].create()
    post_meta.tables['GIP__e_ps'].columns['segment_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['GIP__e_ps'].columns['country_name'].drop()
    post_meta.tables['GIP__e_ps'].columns['segment_id'].drop()

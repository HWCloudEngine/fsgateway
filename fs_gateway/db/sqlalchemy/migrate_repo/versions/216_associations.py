# Copyright 2012 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from migrate.changeset import UniqueConstraint
from migrate import ForeignKeyConstraint
from sqlalchemy import Boolean, BigInteger, Column, DateTime, Enum
from sqlalchemy import ForeignKey, Index, Integer, MetaData, String, Table
from sqlalchemy import Text
from sqlalchemy.types import NullType

from fs_gateway.i18n import _
from fs_gateway.common import log as logging

LOG = logging.getLogger(__name__)


# Note on the autoincrement flag: this is defaulted for primary key columns
# of integral type, so is no longer set explicitly in such cases.

def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    users = Table('users', meta,
        Column('created_at', DateTime(timezone=False)),
        Column('updated_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('uuid', String(length=36), nullable=False),
        Column('name', String(length=255), nullable=False),
        Column('password', String(length=255), nullable=False),
        Column('description', String(length=1023)),
        Column('region', String(length=255), nullable=False),
        Column('deleted', Integer),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    project_association = Table('project_association', meta,
        Column('created_at', DateTime(timezone=False)),
        Column('updated_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('uuid', String(length=36), nullable=False),
        Column('hproject', String(length=36), nullable=False),
        Column('userid', String(length=36), ForeignKey("users.uuid"), nullable=False),
        Column('project', String(length=36), nullable=False),
        Column('region', String(length=255), nullable=False),
        Column('deleted', Integer),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    flavor_association = Table('flavor_association', meta,
        Column('created_at', DateTime(timezone=False)),
        Column('updated_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('uuid', String(length=36), nullable=False),
        Column('hflavor', String(length=36), nullable=False),
        Column('flavor', String(length=36), nullable=False),
        Column('region', String(length=255), nullable=False),
        Column('deleted', Integer),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    image_association = Table('image_association', meta,
        Column('created_at', DateTime(timezone=False)),
        Column('updated_at', DateTime(timezone=False)),
        Column('deleted_at', DateTime(timezone=False)),
        Column('id', Integer, primary_key=True, nullable=False),
        Column('uuid', String(length=36), nullable=False),
        Column('himage', String(length=36), nullable=False),
        Column('image', String(length=36), nullable=False),
        Column('region', String(length=255), nullable=False),
        Column('deleted', Integer),
        mysql_engine='InnoDB',
        mysql_charset='utf8'
    )

    users.create()
    Index('uuid', users.c.uuid, unique=True).create()
    # create all tables
    tables = [project_association, flavor_association, image_association]

    for table in tables:
        try:
            table.create()
        except Exception:
            LOG.info(repr(table))
            LOG.exception(_('Exception while creating table.'))
            raise

    # user
    UniqueConstraint("region", "name", "deleted", table=users,
            name="uniq_user0name0region0deleted").create()
    # project
    UniqueConstraint("hproject", "region", "deleted", table=project_association, 
                                name="uniq_project0hproject0region0deleted").create()
    # flavor
    UniqueConstraint("hflavor", "region", "deleted", table=flavor_association,
                                name="uniq_flavor0hflavor0region0deleted").create()
    # image
    UniqueConstraint("himage", "region", "deleted", table=image_association, 
                                name="uniq_image0himage0region0deleted").create()

    # Common indexes (indexes we apply to all databases)
    # NOTE: order specific for MySQL diff support
    common_indexes = [ ]

    MYSQL_INDEX_SKIPS = [
        # we create this one manually for MySQL above
    ]

    for index in common_indexes:
        if migrate_engine.name == 'postgresql' and \
            index.name in POSTGRES_INDEX_SKIPS:
            continue
        if migrate_engine.name == 'mysql' and \
            index.name in MYSQL_INDEX_SKIPS:
            continue
        else:
            index.create(migrate_engine)

    if migrate_engine.name == 'mysql':
        # In Folsom we explicitly converted migrate_version to UTF8.
        migrate_engine.execute(
            'ALTER TABLE migrate_version CONVERT TO CHARACTER SET utf8')
        # Set default DB charset to UTF8.
        migrate_engine.execute(
            'ALTER DATABASE %s DEFAULT CHARACTER SET utf8' %
            migrate_engine.url.database)



def downgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    for table in ( 'project_association', 'flavor_association', 'image_association', 'users'):
        for prefix in ('', 'shadow_'):
            table_name = prefix + table
            if migrate_engine.has_table(table_name):
                instance_extra = Table(table_name, meta, autoload=True)
                instance_extra.drop()

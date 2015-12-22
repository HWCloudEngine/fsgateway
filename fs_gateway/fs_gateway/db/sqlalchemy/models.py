# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# Copyright 2011 Piston Cloud Computing, Inc.
# All Rights Reserved.
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
"""
SQLAlchemy models for fs_gateway data.
"""

from oslo.config import cfg
from oslo.db.sqlalchemy import models
from sqlalchemy import Column, Index, Integer, BigInteger, Enum, String, schema
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import orm
from sqlalchemy import ForeignKey, DateTime, Boolean, Text, Float

from fs_gateway.db.sqlalchemy import types
from fs_gateway.common import timeutils

BASE = declarative_base()


def MediumText():
    return Text().with_variant(MEDIUMTEXT(), 'mysql')


class GWBase(models.SoftDeleteMixin,
               models.TimestampMixin,
               models.ModelBase):
    metadata = None

    # TODO(ekudryashova): remove this after both fs_gateway and oslo.db
    # will use oslo.utils library
    # NOTE: Both projects(fs_gateway and oslo.db) use `timeutils.utcnow`, which
    # returns specified time(if override_time is set). Time overriding is
    # only used by unit tests, but in a lot of places, temporarily overriding
    # this columns helps to avoid lots of calls of timeutils.set_override
    # from different places in unit tests.
    created_at = Column(DateTime, default=lambda: timeutils.utcnow())
    updated_at = Column(DateTime, onupdate=lambda: timeutils.utcnow())

    def save(self, session=None):
        from fs_gateway.db.sqlalchemy import api

        if session is None:
            session = api.get_session()

        super(GWBase, self).save(session=session)


class User(BASE, GWBase):
    """Represents a user."""
    __tablename__ = "users"
    __table_args__ = (
        # Index('uuid', 'uuid', unique=True), 
        schema.UniqueConstraint("region", "name", "deleted",
                                name="uniq_user0name0region0deleted"), 
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=True)
    name = Column(String(255), nullable=True)
    password = Column(String(255), nullable=True)
    region = Column(String(255), nullable=True)
    description = Column(String(1023))


class ProjectAssociation(BASE, GWBase):
    """Represents a project association."""
    __tablename__ = "project_association"
    __table_args__ = (
        # schema.UniqueConstraint("uuid", "deleted", name="uniq_project0uuid0deleted"), 
        schema.UniqueConstraint("hproject", "region", "deleted",
                                name="uniq_project0hproject0region0deleted"), 
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=True)
    hproject = Column(String(36), nullable=True)
    userid = Column(String(36), ForeignKey("users.uuid"), nullable=False)
    project = Column(String(36), nullable=True)
    region = Column(String(255), nullable=True)

class FlavorAssociation(BASE, GWBase):
    """Represents a flavor association."""
    __tablename__ = "flavor_association"
    __table_args__ = (
        Index('uuid', 'uuid', unique=True),
        # schema.UniqueConstraint("uuid", "deleted",
                                # name="uniq_flavor0assoc_id0deleted"), 
        schema.UniqueConstraint("hflavor", "region", "deleted",
                                name="uniq_flavor0hflavor0region0deleted"), 
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=True)
    hflavor = Column(String(36), nullable=True)
    flavor = Column(String(36), nullable=True)
    region = Column(String(255), nullable=True)

class ImageAssociation(BASE, GWBase):
    """Represents a image association."""
    __tablename__ = "image_association"
    __table_args__ = (
        # schema.UniqueConstraint("uuid", "deleted",
                                # name="uniq_image0assoc_id0deleted"), 
        schema.UniqueConstraint("himage", "region", "deleted",
                                name="uniq_image0himage0region0deleted"), 
    )

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=True)
    himage = Column(String(36), nullable=True)
    image = Column(String(36), nullable=True)
    region = Column(String(255), nullable=True)

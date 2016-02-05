# Copyright (c) 2011 X.commerce, a business unit of eBay Inc.
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
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

"""Defines interface for DB access.

Functions in this module are imported into the fs_gateway.db namespace. Call these
functions from fs_gateway.db namespace, not the fs_gateway.db.api namespace.

All functions in this module return objects that implement a dictionary-like
interface. Currently, many of these objects are sqlalchemy objects that
implement a dictionary interface. However, a future goal is to have all of
these objects be simple dictionaries.

"""

from oslo.config import cfg
from oslo.db import concurrency

from fs_gateway.i18n import _
from fs_gateway.common import log as logging


db_opts = [
]

CONF = cfg.CONF
CONF.register_opts(db_opts)

_BACKEND_MAPPING = {'sqlalchemy': 'fs_gateway.db.sqlalchemy.api'}


IMPL = concurrency.TpoolDbapiWrapper(CONF, backend_mapping=_BACKEND_MAPPING)

LOG = logging.getLogger(__name__)

# The maximum value a signed INT type may have
MAX_INT = 0x7FFFFFFF

###################

def user_get(context, id):
    return IMPL.user_get(context, id)

def user_create(context, values):
    """Create a user from the values dictionary."""
    return IMPL.user_create(context, values)

def user_delete(context, id):
    """Destroy the user or raise if it does not exist."""
    return IMPL.user_delete(context, id)

def user_update(context, id, values):
    return IMPL.user_update(context, id, values)

def user_get_all(context):
    """get all users."""
    return IMPL.user_get_all(context)

###################

def association_get(context, id, name):
    return IMPL.association_get(context, id, name)

def association_create(context, values, name):
    """Create a association from the values dictionary."""
    return IMPL.association_create(context, values, name)

def association_delete(context, id, name):
    """Destroy the association or raise if it does not exist."""
    return IMPL.association_delete(context, id, name)

def association_update(context, id, values, name):
    return IMPL.association_update(context, id, values, name)

def association_get_all(context, name):
    """get all associations. """
    return IMPL.association_get_all(context, name)

def association_get_by_filter(context, resource_name, **search_opts):
    return IMPL.association_get(context, resource_name, **search_opts)

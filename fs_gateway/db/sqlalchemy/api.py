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

"""Implementation of SQLAlchemy backend."""

import collections
import copy
import datetime
import functools
import sys
import threading
import time
import uuid

from oslo.config import cfg
from oslo.db import exception as db_exc
from oslo.db.sqlalchemy import session as db_session
from oslo.db.sqlalchemy import utils as sqlalchemyutils
import six
from sqlalchemy import and_
from sqlalchemy import Boolean
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy import Integer
from sqlalchemy import MetaData
from sqlalchemy import or_
from sqlalchemy.orm import contains_eager
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import joinedload_all
from sqlalchemy.orm import noload
from sqlalchemy.orm import undefer
from sqlalchemy.schema import Table
from sqlalchemy import sql
from sqlalchemy.sql.expression import asc
from sqlalchemy.sql.expression import desc
from sqlalchemy.sql import false
from sqlalchemy.sql import func
from sqlalchemy.sql import null
from sqlalchemy.sql import true
from sqlalchemy import String

import fs_gateway.context
from fs_gateway.db.sqlalchemy import models
from fs_gateway import exception
from fs_gateway.i18n import _
from fs_gateway.common import log as logging

db_opts = [
    cfg.StrOpt('fs_gateway_api_name_scope',
               default='',
               help='When set, compute API will consider duplicate hostnames '
                    'invalid within the specified scope, regardless of case. '
                    'Should be empty, "project" or "global".'),
]

CONF = cfg.CONF
CONF.register_opts(db_opts)

LOG = logging.getLogger(__name__)
# LOG.basicConfig(filename='myapp.log', level=LOG.INFO)


_ENGINE_FACADE = None
_LOCK = threading.Lock()

__association_models = { 
    'image' : models.ImageAssociation, 
    'project' : models.ProjectAssociation, 
    'flavor': models.FlavorAssociation,
    'network': models.NetworkAssociation,
    'subnet': models.SubnetAssociation
}


def _create_facade_lazily():
    global _LOCK, _ENGINE_FACADE
    if _ENGINE_FACADE is None:
        with _LOCK:
            if _ENGINE_FACADE is None:
                _ENGINE_FACADE = db_session.EngineFacade.from_config(CONF)
    return _ENGINE_FACADE


def get_engine(use_slave=False):
    facade = _create_facade_lazily()
    return facade.get_engine(use_slave=use_slave)


def get_session(use_slave=False, **kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(use_slave=use_slave, **kwargs)


_SHADOW_TABLE_PREFIX = 'shadow_'
_DEFAULT_QUOTA_NAME = 'default'


def get_backend():
    """The backend is this module itself."""
    return sys.modules[__name__]


def require_context(f):
    """Decorator to require *any* user or admin context.

    This does no authorization for user or project access matching, see
    :py:func:`fs_gateway.context.authorize_project_context` and
    :py:func:`fs_gateway.context.authorize_user_context`.

    The first argument to the wrapped function must be the context.

    """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        fs_gateway.context.require_context(args[0])
        return f(*args, **kwargs)
    return wrapper


def require_aggregate_exists(f):
    """Decorator to require the specified aggregate to exist.

    Requires the wrapped function to use context and aggregate_id as
    their first two arguments.
    """

    @functools.wraps(f)
    def wrapper(context, aggregate_id, *args, **kwargs):
        aggregate_get(context, aggregate_id)
        return f(context, aggregate_id, *args, **kwargs)
    return wrapper


def _retry_on_deadlock(f):
    """Decorator to retry a DB API call if Deadlock was received."""
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        while True:
            try:
                return f(*args, **kwargs)
            except db_exc.DBDeadlock:
                LOG.warn(_("Deadlock detected when running "
                           "'%(func_name)s': Retrying..."),
                           dict(func_name=f.__name__))
                # Retry!
                time.sleep(0.5)
                continue
    functools.update_wrapper(wrapped, f)
    return wrapped


def model_query(context, model, *args, **kwargs):
    """Query helper that accounts for context's `read_deleted` field.

    :param context: context to query under
    :param use_slave: If true, use slave_connection
    :param session: if present, the session to use
    :param read_deleted: if present, overrides context's read_deleted field.
    :param project_only: if present and context is user-type, then restrict
            query to match the context's project_id. If set to 'allow_none',
            restriction includes project_id = None.
    :param base_model: Where model_query is passed a "model" parameter which is
            not a subclass of GWBase, we should pass an extra base_model
            parameter that is a subclass of GWBase and corresponds to the
            model parameter.
    """

    use_slave = kwargs.get('use_slave') or False
    if CONF.database.slave_connection == '':
        use_slave = False

    session = kwargs.get('session') or get_session(use_slave=use_slave)
    read_deleted = kwargs.get('read_deleted') or context.read_deleted
    project_only = kwargs.get('hproject_only', False)

    def issubclassof_gw_base(obj):
        return isinstance(obj, type) and issubclass(obj, models.GWBase)

    base_model = model
    if not issubclassof_gw_base(base_model):
        base_model = kwargs.get('base_model', None)
        if not issubclassof_gw_base(base_model):
            raise Exception(_("model or base_model parameter should be "
                              "subclass of GWBase"))

    query = session.query(model, *args)

    default_deleted_value = base_model.__mapper__.c.deleted.default.arg
    if read_deleted == 'no':
        query = query.filter(base_model.deleted == default_deleted_value)
    elif read_deleted == 'yes':
        pass  # omit the filter to include deleted and active
    elif read_deleted == 'only':
        query = query.filter(base_model.deleted != default_deleted_value)
    else:
        raise Exception(_("Unrecognized read_deleted value '%s'")
                            % read_deleted)

    return query

###################

def _user_get(context, id, session=None, read_deleted='no'):
    result = model_query(context, models.User, session=session, read_deleted='no').\
               filter_by(uuid=id).\
                first()
    if not result:
        raise exception.UserNotFound(id = id)
    return result

@require_context
def user_get(context, id):
    try:
        result = _user_get(context, id)
    except db_exc.DBError:
        msg = _("Invalid User id %s in request") % id
        LOG.warn(msg)
        raise exception.InvalidID(id=id)
    return result


@require_context
def user_create(context, values):
    user_ref = models.User()
    user_ref.update(values)
    try:
        user_ref.save()
    except db_exc.DBDuplicateEntry as e:
        raise exception.UserExists(region=values['region'], name=values['name'])
    except db_exc.DBReferenceError as e:
        raise exception.IntegrityException(msg=str(e))
    except db_exc.DBError as e:
        LOG.exception('DB error:%s', e)
        raise exception.UserCreateFailed()
    return dict(user_ref)

@require_context
def user_update(context, id, values):
    session = get_session()
    with session.begin():
        user_ref = _user_get(context, id, session=session)
        if not user_ref:
            raise exception.UserNotFound(id=id)
        new_region = values.get('region', user_ref.get('region', ''))
        new_name = values.get('name', user_ref.get('name', ''))
        user_ref.update(values)
        try:
            user_ref.save(session=session)
        except db_exc.DBDuplicateEntry:
            raise exception.UserExists(region=new_region, name=new_name)

    return dict(user_ref)

@require_context
def user_get_all(context):
    users = model_query(context, models.User).\
                     all()
    return [dict(r) for r in users ]

def user_delete(context, id):
    session = get_session()
    with session.begin():
        user_ref = _user_get(context, id, session=session)
        if not user_ref:
            raise exception.UserNotFound(id=id)

        result = model_query(context, models.ProjectAssociation, session=session, 
                               read_deleted='no').\
                    filter_by(userid=id).count()
        if result > 0:
            raise exception.UserInUse(id=id)
        #user_ref.soft_delete(session=session)
        session.delete(user_ref)

################### associations 

def _association_get_model(obj):
    return __association_models.get(obj)

def _association_query(context, id, obj, session=None):
    result = model_query(context, _association_get_model(obj), session=session).\
               filter_by(uuid=id).\
                first()
    if not result:
        raise exception.AssociationNotFound(id = id, obj=obj)
    return result

@require_context
def association_get(context, id, obj):
    try:
        result = _association_query(context, id, obj)
    except db_exc.DBError:
        msg = _("Invalid %s association id %s in request") % (obj, id)
        LOG.warn(msg)
        raise exception.InvalidID(id=id)
    return result

@require_context
def association_create(context, values, obj):
    _association_ref = _association_get_model(obj)()
    _association_ref.update(values)
    try:
        _association_ref.save()
    except db_exc.DBDuplicateEntry as e:
        raise exception.AssociationExists(region=values['region'], obj=obj, name=values['h'+obj])
    except db_exc.DBReferenceError as e:
        raise exception.IntegrityException(msg=str(e))
    except db_exc.DBError as e:
        LOG.exception('DB error:%s', e)
        raise exception.AssociationCreateFailed()
    return dict(_association_ref)

@require_context
def association_update(context, id, values, obj):
    session = get_session()
    with session.begin():
        _association_ref = _association_query(context, id, obj, session=session)
        if not _association_ref:
            return exception.AssociationNotFound(id=uuid, obj=obj)
        new_name = values.get('h'+obj, _association_ref['h'+obj])
        new_region = values.get('region', _association_ref['region'])
        _association_ref.update(values)
        try:
            _association_ref.save(session=session)
        except db_exc.DBDuplicateEntry:
            raise exception.AssociationExists(region=new_region, obj=obj, name=new_name)
    return _association_ref

@require_context
def association_get_all(context, obj):
    _associations = model_query(context, _association_get_model(obj)).\
                     all()
    return [ dict(r) for r in _associations ]

@require_context
def association_delete(context, id, obj):
    session = get_session()
    with session.begin():
        _association_ref = _association_query(context, id, obj, session=session)
        if not _association_ref:
            return exception.AssociationNotFound(id=uuid, obj=obj)
        #_association_ref.soft_delete(session=session)
        session.delete(_association_ref)


@require_context
def association_get_by_hid(context, hid, obj):
    filter = {'h' + obj : hid }

@require_context
def association_get_by_filter(context, resource_name, **search_opts):
    _associations = model_query(context, _association_get_model(resource_name)).\
               filter_by(**search_opts)
    return [ dict(r) for r in _associations ]

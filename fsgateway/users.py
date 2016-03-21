import webob
from fsgateway import exception
from fsgateway import wsgi
from fsgateway import db
from fsgateway import context as contextUtil

import uuid

from fsgateway.views import users as users_view

def _gen_uuid():
    return unicode(uuid.uuid4())

from FSComponentUtil import crypt

class UserController(wsgi.Application):
    _view_builder_class = users_view.ViewBuilder
    _no_null_fields = ['name', 'password', 'region']
    
        
    def list(self, request):
        return self._view_builder.detail(request, db.user_get_all(contextUtil.get_admin_context()))

    def get_user(self, request, user_id):
        user = db.user_get(contextUtil.get_admin_context(), user_id)
        return self._view_builder.show(request, user)

    def create_user(self, request, user):
        if 'uuid' not in user:
            user['uuid'] = _gen_uuid()
        if 'password' in user:
            user['password'] = crypt.encrypt(user['password'])
        result = db.user_create(contextUtil.get_admin_context(), user)
        return self._view_builder.show(request, result)

    def update_user(self, request, user_id, user):
        if 'password' in user:
            user['password'] = crypt.encrypt(user['password'])
        result = db.user_update(contextUtil.get_admin_context(), user_id, user)
        return self._view_builder.show(request, result)

    def delete_user(self, request, user_id):
        db.user_delete(contextUtil.get_admin_context(), user_id)
        return webob.Response(status_int=204)

def create_router(mapper):
    user_controller = UserController()
    mapper.connect('/users',
                   controller=user_controller,
                   action='list',
                   conditions=dict(method=['GET']))
    mapper.connect('/users',
                   controller=user_controller,
                   action='create_user',
                   conditions=dict(method=['POST']))
    mapper.connect('/users/{user_id}',
                   controller=user_controller,
                   action='get_user',
                   conditions=dict(method=['GET']))
    mapper.connect('/users/{user_id}',
                   controller=user_controller,
                   action='update_user',
                   conditions=dict(method=['PUT']))
    mapper.connect('/users/{user_id}',
                   controller=user_controller,
                   action='delete_user',
                   conditions=dict(method=['DELETE']))

def user_info(user_id):
    user = db.user_get(contextUtil.get_admin_context(), user_id)
    if user:
        password = user["password"]
        try:
            password = crypt.decrypt(password)
        except Exception:
            pass

        return (user["name"],  password)

    return (None, None, None)

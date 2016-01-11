import webob.dec
import wsgi
from fs_gateway.common import log as logging
from keystoneclient.v2_0 import client as kc
from wsgi import render_response
import traceback
from oslo.config import cfg
from oslo.utils import timeutils

LOG = logging.getLogger(__name__)

CONF = cfg.CONF

from fs_gateway.utils import get_project_id
from fs_gateway.association import project_association as project_mapping
from fs_gateway import users
from fs_gateway.common import excutils
from keystoneclient.openstack.common.apiclient import exceptions
from fs_gateway.repoze_lru import ExpiringLRUCache as expire_lru, LRUCache as lru

# Mapping: cascading token => cascaded(project_id, username, password)
cascading_token_to_user = lru(10000)

# Mapping: (project_id, username, password) => cascaded token
user_to_cascaded_token = expire_lru(10000)

class TokenMappingMiddleware(wsgi.Middleware):

    def _get_cascading_tenant_id(self, req):
        cascading_tenant_id = get_project_id(req)
        old_token = req.environ.get('HTTP_X_AUTH_TOKEN')
        if not cascading_tenant_id:
            try:
                kwargs = {
                            'username':CONF.get('cascading_admin_user'),
                            'password': CONF.get('cascading_admin_password'), 
                            'auth_url': CONF.get('cascading_keystone_url'),
                            'insecure': True,
                            'tenant_name': CONF.get('cascading_tenant_name')
                }
                LOG.info('the kwargs is %s' %str(kwargs))
                keystoneclient = kc.Client(**kwargs)
                cascading_tenant_id = None
                # token_info = keystoneclient.authenticate(token=old_token)
                token_info = keystoneclient.tokens._get(kwargs['auth_url'] + "/tokens/%s" % old_token, 'access')
                
                cascading_tenant_id = token_info.tenant['id']
            except AttributeError:
                cascading_tenant_id = None
                pass
            except exceptions.NotFound:
                LOG.info('############### token not found ##########################')
                with excutils.save_and_reraise_exception():
                    LOG.error('get cascading tenant id failed.exception is %s' %traceback.format_exc())   
            except Exception as e:
                LOG.error('get cascading tenant id failed.exception is %s' %traceback.format_exc())
        return cascading_tenant_id

    @webob.dec.wsgify
    def __call__(self, req):
      
        old_token = req.environ.get('HTTP_X_AUTH_TOKEN')
        user_info = cascading_token_to_user.get(old_token)
        new_token = None
        expire = CONF.get('cascaded_token_expiration')
        try:
            cascading_tenant_id = self._get_cascading_tenant_id(req)
        except exceptions.NotFound:
            cascading_token_to_user.invalidate(old_token)
            return render_response(status=(401, 'Unauthorized'))
        req.environ['CASCADING_TENANT_ID'] = cascading_tenant_id
        region = req.environ.get('REGION')
        if user_info:
            req.environ['CASCADED_TENANT_ID'] = user_info[0]
            new_token = user_to_cascaded_token.get(user_info)
        if not new_token:
            if not user_info:
                user_info = (None, None, None)
                if cascading_tenant_id:
                    req.environ['CASCADING_TENANT_ID'] = cascading_tenant_id
                    
                    cascaded_tenant_id, user_id =  project_mapping(cascading_tenant_id, region)
                    if user_id:
                        user_info = (cascaded_tenant_id, ) + users.user_info(user_id)
                    req.environ['CASCADED_TENANT_ID'] = cascaded_tenant_id

                if not cascading_tenant_id or not cascaded_tenant_id:
                    LOG.error('cascading_tenant_id or cascaded_tenant_id  is None')
                    return render_response(status=(500, 'fs_gateway service error'))
                cascading_token_to_user.put(old_token, user_info)

            issued_at = timeutils.isotime()
            before = timeutils.utcnow_ts()
            new_token_info = self._create_token(region,*user_info)
            if 'expires' in new_token_info.token:
                if 'issued_at' in new_token_info.token:
                    issued_at = new_token_info.token['issued_at']

                expire = timeutils.delta_seconds(
                            timeutils.parse_isotime(issued_at),
                            timeutils.parse_isotime(new_token_info.token['expires'])) 
                latency = timeutils.utcnow_ts() - before
                expire -= latency

            new_token = new_token_info.id
            assert new_token, "new token is None"
            user_to_cascaded_token.put(user_info, new_token, timeout=expire)
    
        req.environ['HTTP_X_AUTH_TOKEN'] = new_token
        response = req.get_response(self.application)

        return response

    def _create_token(self, region,cascaded_tenant_id, username, password):
        # if find the mapping cascaded_tenant_id use the cascaded_tenant_id,
        # else use the admin
        
        cascaded_keystone_url = CONF.get('cascaded_keystone_url_map')[region]

        kwargs = {
                    'auth_url': cascaded_keystone_url,
                    'tenant_id': cascaded_tenant_id,
                    'username': username,
                    'password': password,
                    'insecure': True
                }
        LOG.info('the kwargs is %s' %str(kwargs))
        keystoneclient = kc.Client(**kwargs)

        token_info = keystoneclient.tokens.authenticate(username=username,
                                                        tenant_id=cascaded_tenant_id,
                                                        password=password,
                                                        token=None, return_raw=False)

        return token_info

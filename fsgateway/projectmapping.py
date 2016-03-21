import webob.dec
import wsgi
import re
from fsgateway.common import log as logging
from keystoneclient.v2_0 import client as kc
import traceback
LOG = logging.getLogger(__name__)

from oslo.config import cfg
CONF = cfg.CONF
CONF.import_opt('cascading_keystone_url', 'fsgateway.tokenmapping')
CONF.import_opt('cascading_admin_user', 'fsgateway.tokenmapping')


LOG = logging.getLogger(__name__)


from fsgateway.association import project_association as project_mapping

from utils import get_project_id


class ProjectMappingMiddleware(wsgi.Middleware):

    @webob.dec.wsgify
    def __call__(self, req):

        cascading_tenant_id = req.environ.get('CASCADING_TENANT_ID')
        if cascading_tenant_id:
            cascaded_tenant_id = req.environ.get('CASCADED_TENANT_ID')
            LOG.debug('the cascaded tenant id is %s', cascaded_tenant_id)
            if not cascaded_tenant_id:
                LOG.warn("can't found mapping for tenant id %s", cascading_tenant_id)
                cascaded_tenant_id = cascading_tenant_id
        
    
            for field in ('PATH_INFO', 'QUERY_STRING', 'RAW_PATH_INFO'):
                if req.environ.get(field):
                    req.environ[field] = req.environ[field].replace(cascading_tenant_id,cascaded_tenant_id)
            if req.body:
                s = "tenant_id"
                for q in "\"'":
                    idx = req.body.lower().find("%s%s%s:" % (q, s.lower(), q))
                    if idx > 0:
                        break
                old_project = req.body[idx: req.body.find(',', idx+1)].split()
                if len(old_project) > 1:
                    old_project_id = old_project[1].strip("\"'},")
                    if old_project_id == cascading_tenant_id:
                        new_project_id = cascaded_tenant_id
                    else:
                        region = req.environ.get('REGION')
                        new_project_id, unused_user_id =  project_mapping(old_project_id, region)
                    
                    if new_project_id:
                        req.body = bytes(req.body.replace(old_project_id, new_project_id))
        response = req.get_response(self.application)
        return response

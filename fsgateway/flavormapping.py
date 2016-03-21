import webob.dec
import wsgi
from fsgateway.common import log as logging
import re
LOG = logging.getLogger(__name__)

from fsgateway.association import flavor_association as flavor_mapping

from utils import get_flavor_id

class FlavorMappingMiddleware(wsgi.Middleware):

    @webob.dec.wsgify
    def __call__(self, req):
        old_flavor_id = get_flavor_id(req)
        if old_flavor_id:
            region = req.environ.get('REGION')
            new_flavor_id = flavor_mapping(old_flavor_id, region)
            LOG.debug('the cascaded flavor id is %s' %new_flavor_id)
            if new_flavor_id:
                if req.body:
                    s = "flavorRef"
                    for q in "\"'":
                        idx = req.body.lower().find("%s%s%s:" % (q, s.lower(), q))
                        if idx > 0:
                            break
                    old_flavor_str = req.body[idx: req.body.find(',', idx+1)]
                    new_flavor_str = '"%s": "%s"'%(s, str(new_flavor_id))
                    
                    req.body = bytes(req.body.replace(old_flavor_str, new_flavor_str))
            else:
                LOG.warn("can't found mapping for flavor id %s" % old_flavor_id)
                new_flavor_id = old_flavor_id
        
        response = req.get_response(self.application)

        return response

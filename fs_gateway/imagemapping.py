import webob.dec
import wsgi
import re

from fs_gateway.common import log as logging

LOG = logging.getLogger(__name__)

from fs_gateway.utils import get_image_id
from fs_gateway.association import image_association as image_mapping

class ImageMappingMiddleware(wsgi.Middleware):

    @webob.dec.wsgify
    def __call__(self, req):

        http_host = req.environ.get('HTTP_HOST')
        LOG.debug('the request http_host is %s' %http_host) 
        host_info = http_host.rpartition('.')[0].partition('.')
        region = host_info[-1].rpartition('.')[0]
        LOG.debug('the region is %s' %region) 
        if region:
            req.environ['REGION'] = region
        old_image_id = get_image_id(req)
        if old_image_id:
            new_image_id = image_mapping(old_image_id, region)
            LOG.debug('the cascaded image id is %s' %new_image_id)
            if new_image_id:
                prefix = "images/"
                req.environ['PATH_INFO'] = req.environ['PATH_INFO']. \
                            replace(prefix + old_image_id, prefix + new_image_id, 1)
                if req.body:
                    s = "imageRef"
                    for q in "\"'":
                        idx = req.body.lower().find("%s%s%s:" % (q, s.lower(), q))
                        if idx > 0:
                            break
                    old_image_str = req.body[idx: req.body.find(',', idx+1)]
                    new_image_str = '"%s": "%s"'%(s, new_image_id)
                    
                    req.body = bytes(req.body.replace(old_image_str, new_image_str))                 
            else:
                LOG.warn("can't found mapping for image id %s" % old_image_id)
                new_image_id = old_image_id

        response = req.get_response(self.application)
        return response


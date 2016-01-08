import webob.dec
import wsgi
from fs_gateway.common import log as logging
import re
from oslo.config import cfg

CONF = cfg.CONF

opts = [
        cfg.BoolOpt('external_network_mapping_enabled', 
            default=False,
            help='Enable external network mapping')
        ]
CONF.register_opts(opts)

LOG = logging.getLogger(__name__)

from fs_gateway.association import get_association_by_csd , get_association_by_hid


_version_re = r'^/+v[-0-9.]+/+'
_network_path_re = re.compile(_version_re + r'(network|subnet)s')
_network_query_re = re.compile('name=(network|subnet)%40([-0-9a-zA-Z]+)')


def get_network_id(name, hid, region):
    csd = get_association_by_hid(hid, region, name)
    return csd

def get_network_hid(name, csd, region):
    hid = get_association_by_csd(csd, region, name)
    return hid


class NetworkMappingMiddleware(wsgi.Middleware):

    @webob.dec.wsgify
    def __call__(self, req):
        env = req.environ
        region = env.get('REGION')
        name = ''
        path_match = CONF.get('external_network_mapping_enabled') and _network_path_re.search(env.get('PATH_INFO'))
        if path_match:
            name = path_match.group(1)
            def _query_replace(match):
                name, id = match.groups()
                csd_id = get_network_id(name, id, region)
                return 'id=' + csd_id if csd_id else match.group(0)

            if env.get('QUERY_STRING'): # replace QUERY_STRING
                env['QUERY_STRING'] = _network_query_re.sub(_query_replace, env['QUERY_STRING'])

            if env.get('REQUEST_METHOD').lower() == 'delete':
                id_string = env.get('PATH_INFO')[path_match.end():].strip('/')
                if '.' in id_string:
                    id_string = id_string[:id_string.find('.')] # strip .json
                hid = get_network_hid(name, id_string, region)
                if hid:  ## DELETE subnet or network 
                    LOG.debug('### intercept %s delete operation %s', name, id_string)
                    return wsgi.render_response()
        
        response = req.get_response(self.application)

        if name:
            resp_dict = response.json_body
            updated = False
            for net in resp_dict.get(name + 's', [resp_dict.get(name)]):
                if type(net) is dict and 'name' in net and 'id' in net:
                    csd = net['id']
                    hid = get_network_hid(name, csd, region)
                    if hid:
                        net['name'] = name + '@' + hid
                        updated = True
            if updated:
                response.json_body = resp_dict

        return response

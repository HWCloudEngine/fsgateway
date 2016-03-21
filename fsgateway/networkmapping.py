import webob.dec
import wsgi
from fsgateway.common import log as logging
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

from fsgateway.association import association_get_hids_by_csd, association_get_csd_by_hid


_version_re = r'^/+v[-0-9.]+/+'
_network_path_re = re.compile(_version_re + r'(network|subnet)s')


def get_network_id(name, hid, region):
    csd = association_get_csd_by_hid(hid, region, name)
    return csd

def get_network_hid(name, csd, region):
    hid_list = association_get_hids_by_csd(csd, region, name)
    if hid_list and len(hid_list) > 1:
        LOG.warn("Resource %s for region %s csd id %s has multiple hybrid ids: %s", 
                name, region, csd, hid_list)
    return hid_list[0] if hid_list else None


class NetworkMappingMiddleware(wsgi.Middleware):

    @webob.dec.wsgify
    def __call__(self, req):
        env = req.environ
        path_match = CONF.get('external_network_mapping_enabled') and _network_path_re.search(env.get('PATH_INFO'))
        if not path_match:
            response = req.get_response(self.application)
            return response
        region = env.get('REGION')
        name = path_match.group(1)

        csd = env.get('PATH_INFO')[path_match.end():].strip('/')
        if '.' in csd:
            csd = csd[:csd.find('.')] # strip .json
        if len(csd) < 3:
            csd = ''
        hid = ''

        method = env.get('REQUEST_METHOD').upper()
        if method == 'GET':  # List, Get
            name_field = req.GET.get('name', '')  # query name 
            if name_field.startswith(name + '@'):
                # replace QUERY_STRING
                hid = name_field[len(name) + 1:]
                if not csd:
                    csd = get_network_id(name, hid, region)
                if csd:
                    LOG.info("### update %s query string %s (hybrid %s)", name, csd, hid)
                    env['QUERY_STRING'] = env['QUERY_STRING'].replace(
                                            'name=' + name + '%40' + hid, 'id='+ csd)

        elif method == 'DELETE': # Delete
            hid = get_network_hid(name, csd, region)
            if hid:  ## DELETE subnet or network 
                LOG.debug('### intercept %s delete %s (hybrid %s)', name, csd, hid)
                return wsgi.render_response()

        elif method == 'POST':  # Single or bulk create
            json_body = req.json_body
            network_or_subnets = json_body.get(name + 's', [json_body.get(name,[])])
            for net in network_or_subnets:
                req_name = net.get('name', '')
                if req_name.startswith(name + '@'):
                    hid = req_name[len(name)+1:]
                    csd = get_network_id(name, hid, region)
                    LOG.info("POST %s for %s (hybrid %s)", name, csd, hid)
                    if csd:  # translate into a show operation
                        LOG.warn("POST %s action from proxy for %s (hybrid  %s),"
                                 " please check the association!!",
                                 name, csd, hid)
                        pass # TODO

        elif method == 'PUT':  # Update
            # import pdb;pdb.set_trace()
            hid = get_network_hid(name, csd, region)
            if hid:
                LOG.warn("PUT %s action from proxy for %s (hybrid %s)",
                        name, csd, hid)

                # TODO
                render_response(status=(200, 'Success'), 
                        body='{"network":{"id":"%s", "name" : "%s"}}' % (csd, name + '@' + hid))

        response = req.get_response(self.application)

        resp_dict = response.json_body
        updated = False

        # for list and mutiple hybrid resource associating with the same cascaded resoure
        for net in resp_dict.get(name + 's', [resp_dict.get(name)]):
            if type(net) is dict and 'name' in net and 'id' in net:
                if net['name'] == name + '@' + hid: # no need to fix
                    continue
                _csd = net['id']
                _hid = (csd == _csd and hid) or get_network_hid(name, _csd, region)
                if _hid:
                    net['name'] = name + '@' + _hid
                    updated = True
                    LOG.info('### response update %s, %s (hybrid %s)', name, _csd, _hid)
        if updated:
            response.json_body = resp_dict
            LOG.debug('### updated response %s ', response.body)

        return response

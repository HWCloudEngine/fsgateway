import os
import webob

from webob import Request
from webob import Response
from wsgi import render_response
import requests
import traceback

import logging

LOG = logging.getLogger(__name__)

from fs_gateway.wsgiproxy.app import WSGIProxyApp
from keystoneclient.v2_0 import client as kc

from oslo.config import cfg
CONF = cfg.CONF

service_type_mapping = {
                        'backup':'backup',
                        'metering':'metering',
                        'volume' :'volume',
                        'volumev2' :'volumev2',
                        'collect':'collect',
                        'cps' :'cps',
                        'ec2':'ec2',
                        'elb':'elb',
                        'oam':'oam',
                        'image':'image',
                        's3':'s3',
                        'orchestration' :'orchestration',
                        'baremetal':'baremetal',
                        'identity':'identity',
                        'log':'log',
                        'network':'network',
                        'compute':'compute',
                        's3':'s3',
                        'object-store' :'object-store',
                        'upgrade':'upgrade'
                    }


tenant_name = 'admin'

user_name ='cloud_admin'
password = 'FusionSphere123'

class fs_gateway():
    def __init__(self):
        pass
    def __call__(self, environ, start_response):
        #print("the environ of request is %s " %str(environ))
        #print ('the function of request is %s ' %environ.get('REQUEST_METHOD'))
        try:
            cascading_keystone_url = CONF.get('cascading_keystone_url')
            tenant_name = CONF.get('cascading_tenant_name')
            user_name = CONF.get('cascading_admin_user')
            password = CONF.get('cascading_admin_password')
            http_host = environ.get('HTTP_HOST')
            host_info = http_host.rpartition('.')[0].partition('.')
            region = host_info[-1].rpartition('.')[0]
            service_type_info = host_info[0].rpartition('--')[-1]
            service_type =service_type_mapping.get(service_type_info)

            kwargs = {
                        'auth_url': cascading_keystone_url,
                        'tenant_name': tenant_name,
                        'username': user_name,
                        'password': password,
                        'insecure': True
                    }
            LOG.debug('the kwargs is %s' %str(kwargs))
            keystoneclient = kc.Client(**kwargs)
            management_url = keystoneclient.service_catalog.url_for(service_type=service_type,
                                                          attr='region',
                                                          endpoint_type='publicURL',
                                                          filter_value=region)

            proc = 'https://'
            for p in ['http://', 'https://']:
                if management_url.startswith(p):
                    proc, management_url = p, management_url[len(p):]
                    break
            if '/' in management_url:
                management_url = management_url[:management_url.find('/')]
            management_url = proc + management_url
            LOG.debug('the management_url is %s' %management_url)
        except Exception:
            LOG.error('find the mamagement_url failed %s' %traceback.format_exc())
            return render_response(status=(500, 'fs_gateway service error'))
        app = WSGIProxyApp(management_url)
        resp = app(environ,start_response)
        LOG.debug('the result is %s ' %str(resp))
        return resp

    @classmethod
    def factory(cls, global_config, **local_config):
        """Simple paste factory, :class:`fs_gateway.wsgi.Router` doesn't have one."""

        return cls()

#     def _get_management_url(self, kc, **kwargs):
#         return kc.service_catalog.url_for(**kwargs)

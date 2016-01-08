import webob
import wsgi
import db
import context as contextUtil

defaultContext = contextUtil.get_admin_context()

import uuid

from fs_gateway.views import association as association_view

_resource_names = ('project', 'image', 'network','flavor', 'subnet')

def _gen_uuid():
    return unicode(uuid.uuid4())

class Controller(wsgi.Application):

    def __init__(self, name):
        super(Controller, self).__init__()
        self.name = name
        self._view_builder = association_view.ViewBuilder(name)
        
    def list(self, request):
        return self._view_builder.detail(request, 
                db.association_get_all(defaultContext, self.name))

    def get(self, request, association_id):
        association = db.association_get(defaultContext, association_id, self.name)
        return self._view_builder.show(request, association)

    def create(self, request, association):
        if 'uuid' not in association:
            association['uuid'] = _gen_uuid()
        result = db.association_create(defaultContext, association, self.name)
        return self._view_builder.show(request, result)

    def update(self, request, association_id, association):
        result = db.association_update(defaultContext, 
                    association_id, association, self.name);
        return self._view_builder.show(request, result)

    def delete(self, request, association_id):
        db.association_delete(defaultContext, association_id, self.name)
        return webob.Response(status_int=204)

def create_router(mapper):

    for p in _resource_names:
        controller = Controller(p)

        path = '/%s_association' % p
        mapper.connect(path,
                       controller=controller,
                       action='list',
                       conditions=dict(method=['GET']))
        mapper.connect(path,
                       controller=controller,
                       action='create',
                       conditions=dict(method=['POST']))
        mapper.connect(path + '/{association_id}',
                       controller=controller,
                       action='get',
                       conditions=dict(method=['GET']))
        mapper.connect(path + '/{association_id}',
                       controller=controller,
                       action='update',
                       conditions=dict(method=['PUT']))
        mapper.connect(path + '/{association_id}',
                       controller=controller,
                       action='delete',
                       conditions=dict(method=['DELETE']))


def _filter_by_region(assocs, region, obj):
    res = {}
    if assocs:
        for a in assocs:
            if region == a.get('region'):
                res = a
                break
    if obj == 'project':
        return (res.get(obj),  res.get("userid"))
    return res.get(obj)

def get_association_by_csd(id, region, resource_name):
    result = db.association_get_by_csd(defaultContext, id, resource_name)
    return _filter_by_region(result, region, resource_name)

def get_association_by_hid(hid, region, resource_name):
    result = db.association_get_by_hid(defaultContext, hid, resource_name)
    return _filter_by_region(result, region, resource_name)

def project_association(project_id, region):
    return get_association_by_hid(project_id, region, 'project')

def flavor_association(flavor_id, region):
    return get_association_by_hid(flavor_id, region, 'flavor')

def image_association(image_id, region):
    return get_association_by_hid(image_id, region, 'image')

def network_association(network_id, region):
    return get_association_by_hid(network_id, region, 'network')

def subnet_association(subnet_id, region):
    return get_association_by_hid(subnet_id, region, 'subnet')


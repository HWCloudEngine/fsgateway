
import webob
import wsgi
import db
import context as contextUtil

import uuid

from fs_gateway.views import association as association_view

def _gen_uuid():
    return unicode(uuid.uuid4())

class ProjectController(wsgi.Application):
    _view_builder_class = association_view.ProjectViewBuilder
        
    def list(self, request):
        associations = db.project_association_get_all(contextUtil.get_admin_context())
        return self._view_builder.detail(request, associations)

    def get(self, request, association_id):
        association = db.project_association_get(contextUtil.get_admin_context(), association_id)
        return self._view_builder.show(request, association)

    def create(self, request, association):
        if 'uuid' not in association:
            association['uuid'] = _gen_uuid()
        result = db.project_association_create(contextUtil.get_admin_context(), association)
        return self._view_builder.show(request, result)

    def update(self, request, association_id, association):
        result = db.project_association_update(contextUtil.get_admin_context(), 
                    association_id, association);
        return self._view_builder.show(request, result)

    def delete(self, request, association_id):
        db.project_association_delete(contextUtil.get_admin_context(), association_id)
        return webob.Response(status_int=204)

class FlavorController(wsgi.Application):
    _view_builder_class = association_view.FlavorViewBuilder
        
    def list(self, request):
        return self._view_builder.detail(request, 
                db.flavor_association_get_all(contextUtil.get_admin_context()))

    def get(self, request, association_id):
        association = db.flavor_association_get(contextUtil.get_admin_context(), association_id)
        return self._view_builder.show(request, association)

    def create(self, request, association):
        if 'uuid' not in association:
            association['uuid'] = _gen_uuid()
        result = db.flavor_association_create(contextUtil.get_admin_context(), association)
        return self._view_builder.show(request, result)

    def update(self, request, association_id, association):
        result = db.flavor_association_update(contextUtil.get_admin_context(), 
                    association_id, association);
        return self._view_builder.show(request, result)

    def delete(self, request, association_id):
        db.flavor_association_delete(contextUtil.get_admin_context(), association_id)
        return webob.Response(status_int=204)

class ImageController(wsgi.Application):
    _view_builder_class = association_view.ImageViewBuilder
        
    def list(self, request):
        return self._view_builder.detail(request, 
                db.image_association_get_all(contextUtil.get_admin_context()))

    def get(self, request, association_id):
        association = db.image_association_get(contextUtil.get_admin_context(), association_id)
        return self._view_builder.show(request, association)
        # association = db.association_get_by_himage(contextUtil.get_admin_context(), association_id)
        # return self._view_builder.detail(request, association)

    def create(self, request, association):
        if 'uuid' not in association:
            association['uuid'] = _gen_uuid()
        result = db.image_association_create(contextUtil.get_admin_context(), association)
        return self._view_builder.show(request, result)

    def update(self, request, association_id, association):
        result = db.image_association_update(contextUtil.get_admin_context(), 
                    association_id, association);
        return self._view_builder.show(request, result)

    def delete(self, request, association_id):
        db.image_association_delete(contextUtil.get_admin_context(), association_id)
        return webob.Response(status_int=204)

def create_router(mapper):

    for p, controller in (('project', ProjectController()), 
                ('image', ImageController()), 
                ('flavor', FlavorController())):

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

def project_association(project_id, region):
    result = db.association_get_by_hproject(contextUtil.get_admin_context(), project_id)
    return _filter_by_region(result, region, 'project')

def flavor_association(flavor_id, region):
    result = db.association_get_by_hflavor(contextUtil.get_admin_context(), flavor_id)
    return _filter_by_region(result, region, 'flavor')

def image_association(image_id, region):
    result = db.association_get_by_himage(contextUtil.get_admin_context(), image_id)
    return _filter_by_region(result, region, 'image')

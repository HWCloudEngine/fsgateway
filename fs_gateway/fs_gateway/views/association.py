# Copyright 2010-2011 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


class ProjectViewBuilder(object):

    _collection_name = "project_association"

    def basic(self, request, assoc):
        return {
            "association": {
                "id": assoc["uuid"],
            },
        }

    def show(self, request, assoc):
        return {
            "association": {
                "id": assoc["uuid"],
                "hproject": assoc["hproject"],
                "project": assoc["project"],
                "region": assoc["region"],
                "userid": assoc["userid"]
            }
        }

    def index(self, request, associations):
        """Return the 'index' view of associations."""
        return self._list_view(self.basic, request, associations)

    def detail(self, request, associations):
        """Return the 'detail' view of associations."""
        return self._list_view(self.show, request, associations)

    def _list_view(self, func, request, associations):
        """Provide a view for a list of association."""
        return dict(associations=[func(request, assoc)["association"] for assoc in associations])

class FlavorViewBuilder(object):

    _collection_name = "flavor_association"

    def basic(self, request, assoc):
        return {
            "association": {
                "id": assoc["uuid"],
            },
        }

    def show(self, request, assoc):
        return {
            "association": {
                "id": assoc["uuid"],
                "hflavor": assoc["hflavor"],
                "flavor": assoc["flavor"],
                "region": assoc["region"],
            }
        }

    def index(self, request, associations):
        """Return the 'index' view of associations."""
        return self._list_view(self.basic, request, associations)

    def detail(self, request, associations):
        """Return the 'detail' view of associations."""
        return self._list_view(self.show, request, associations)

    def _list_view(self, func, request, associations):
        """Provide a view for a list of association."""
        return dict(associations=[func(request, assoc)["association"] for assoc in associations])

class ImageViewBuilder(object):

    _collection_name = "image_association"

    def basic(self, request, assoc):
        return {
            "association": {
                "id": assoc["uuid"],
            },
        }

    def show(self, request, assoc):
        return {
            "association": {
                "id": assoc["uuid"],
                "himage": assoc["himage"],
                "image": assoc["image"],
                "region": assoc["region"],
            }
        }

    def index(self, request, associations):
        """Return the 'index' view of associations."""
        return self._list_view(self.basic, request, associations)

    def detail(self, request, associations):
        """Return the 'detail' view of associations."""
        return self._list_view(self.show, request, associations)

    def _list_view(self, func, request, associations):
        """Provide a view for a list of association."""
        return dict(associations=[func(request, assoc)["association"] for assoc in associations])


# Copyright 2010 Jacob Kaplan-Moss

# Copyright 2011 OpenStack Foundation
# Copyright 2013 IBM Corp.
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

from __future__ import print_function

import argparse
import copy
import datetime
import getpass
import locale
import logging
import os
import sys
import time

from oslo.utils import encodeutils
from oslo.utils import strutils
from oslo.utils import timeutils
import six

from fs_gatewayclient import exceptions
from fs_gatewayclient.i18n import _
from fs_gatewayclient.openstack.common import cliutils
from fs_gatewayclient.openstack.common import uuidutils
from fs_gatewayclient import utils


logger = logging.getLogger(__name__)

###### users
def _print_user_list(users):

    headers = [
        'ID',
        'Name',
        'Region',
        'Description',
    ]

    formatters = {}

    utils.print_list(users, headers, formatters)

def _print_user(user):
    info = user._info.copy()
    # ignore links, we don't need to present those
    
    utils.print_dict(info)

def _find_user(cs, user):
    """Get a user by name, ID."""
    try:
        return utils.find_resource(cs.users, user)
    except exceptions.NotFound as e:
        raise e


def do_user_list(cs, args):
    """Print a list of available 'users'."""
    users = cs.users.list()
    _print_user_list(users)


@utils.arg('user',
    metavar='<user>',
    help=_("Name or ID of the user to delete"))
def do_user_delete(cs, args):
    """Delete a specific user"""
    userid = _find_user(cs, args.user)
    cs.users.delete(userid)
    _print_user_list([userid])


@utils.arg('user',
     metavar='<user>',
     help=_("Name or ID of user"))
def do_user_show(cs, args):
    """Show details about the given user."""
    user = _find_user(cs, args.user)
    _print_user(user)


@utils.arg('name',
     metavar='<name>',
     help=_("Name of the new user"))
@utils.arg('password',
     metavar='<password>',
     help=_("Password of the new user"))
@utils.arg('region',
     metavar='<region>',
     help=_("Region name of the new user"))
@utils.arg('--description',
     metavar='<description>',
     help=_("Description of the user (optional)"))
def do_user_create(cs, args):
    """Create a new user"""
    f = cs.users.create(name=args.name, password=args.password, region=args.region, description=args.description)
    _print_user_list([f])

@utils.arg('id',
     metavar='<id>',
     help=_("ID of the user"))
@utils.arg('--name',
     metavar='<name>',
     help=_("Name of the user (optional)"))
@utils.arg('--pass',
     metavar='<pass>',
     dest='password',
     help=_("Password of the user (optional)"))
@utils.arg('--region',
     metavar='<region>',
     help=_("Region name of the user (optional)"))
@utils.arg('--description',
     metavar='<description>',
     help=_("Description of the user (optional)"))
def do_user_update(cs, args):
    cs.users.update(args.id, name=args.name, 
                    password=args.password,
                    region=args.region, 
                    description=args.description)

###### project association 
def _print_association_list(name, associations):

    headers = [
        'ID', 
        'H' + name.capitalize(),
         name.capitalize(),
        'Region',
    ]
    if name.lower() == 'project':
        headers.append('Userid')

    utils.print_list(associations, headers)

def _print_association(association):
    info = association._info.copy()
    # ignore links, we don't need to present those
    
    utils.print_dict(info)

def _find_association(cs, association):
    """Get a association by name, ID."""
    try:
        return utils.find_resource(cs.associations, association)
    except exceptions.NotFound as e:
        raise e

def do_project_association_list(cs, args):
    """Print a list of available 'project_associations'."""
    name="project"
    cs.associations.set_name(name)
    association = cs.associations.list()
    _print_association_list(name, association)

@utils.arg('project_association',
    metavar='<project_association>',
    help=_("Name or ID of the project_association to delete"))
def do_project_association_delete(cs, args):
    """Delete a specific project_association"""
    name="project"
    cs.associations.set_name(name)
    association = _find_association(cs, args.project_association)
    cs.associations.delete(association)
    _print_association_list(name, [association])


@utils.arg('project_association',
     metavar='<project_association>',
     help=_("Name or ID of project_association"))
def do_project_association_show(cs, args):
    """Show details about the given project_association."""
    name="project"
    cs.associations.set_name(name)
    association = _find_association(cs, args.project_association)
    _print_association(association)

@utils.arg('id',
     metavar='<id>',
     help=_("Id of the project association"))
@utils.arg('--hproject',
     metavar='<hproject>',
     help=_("Cascading project id of the project association "))
@utils.arg('--project',
     metavar='<project>',
     help=_("Cascaded project id of the project association"))
@utils.arg('--userid',
     metavar='<userid>',
     help=_("Userid created by user-create"))
@utils.arg('--region',
     metavar='<region>',
     help=_("Region name of the project association"))
def do_project_association_update(cs, args):
    """Update a project association"""
    name="project"
    cs.associations.set_name(name)
    f = cs.associations.update(args.id, hproject=args.hproject, project=args.project, 
                                region=args.region, userid=args.userid)
    _print_association_list(name, [f])

@utils.arg('hproject',
     metavar='<hproject>',
     help=_("Cascading project id of the new project association"))
@utils.arg('project',
     metavar='<project>',
     help=_("Cascaded project id of the new project association"))
@utils.arg('userid',
     metavar='<userid>',
     help=_("Userid created by user-create"))
@utils.arg('region',
     metavar='<region>',
     help=_("Region name of the new project association"))
def do_project_association_create(cs, args):
    """Create a new project_association"""
    name="project"
    cs.associations.set_name(name)
    info = {
            "hproject" : args.hproject, 
            "project": args.project, 
            "region": args.region, 
            "userid": args.userid
            }
    f = cs.associations.create(**info)
    _print_association_list(name, [f])

###### flavor association 

def _print_association(association):
    info = association._info.copy()
    # ignore links, we don't need to present those
    
    utils.print_dict(info)

def _find_association(cs, association):
    """Get a association by name, ID."""
    try:
        return utils.find_resource(cs.associations, association)
    except exceptions.NotFound as e:
        raise e

def do_flavor_association_list(cs, args):
    """Print a list of available 'flavor_associations'."""
    name="flavor"
    cs.associations.set_name(name)
    association = cs.associations.list()
    _print_association_list(name, association)

@utils.arg('flavor_association',
    metavar='<flavor_association>',
    help=_("Name or ID of the flavor_association to delete"))
def do_flavor_association_delete(cs, args):
    """Delete a specific flavor_association"""
    name="flavor"
    cs.associations.set_name(name)
    association = _find_association(cs, args.flavor_association)
    cs.associations.delete(association)
    _print_association_list(name, [association])


@utils.arg('flavor_association',
     metavar='<flavor_association>',
     help=_("Name or ID of flavor_association"))
def do_flavor_association_show(cs, args):
    """Show details about the given flavor_association."""
    name="flavor"
    cs.associations.set_name(name)
    association = _find_association(cs, args.flavor_association)
    _print_association(association)

@utils.arg('id',
     metavar='<id>',
     help=_("Id of the flavor association"))
@utils.arg('--hflavor',
     metavar='<hflavor>',
     help=_("Cascading flavor id of the flavor association "))
@utils.arg('--flavor',
     metavar='<flavor>',
     help=_("Cascaded flavor id of the flavor association"))
@utils.arg('--region',
     metavar='<region>',
     help=_("Region name of the flavor association"))
def do_flavor_association_update(cs, args):
    """Update a flavor association"""
    name="flavor"
    cs.associations.set_name(name)
    f = cs.associations.update(args.id, hflavor=args.hflavor, 
                                flavor=args.flavor, region=args.region)
    _print_association_list(name, [f])

@utils.arg('hflavor',
     metavar='<hflavor>',
     help=_("Cascading flavor id of the new flavor association"))
@utils.arg('flavor',
     metavar='<flavor>',
     help=_("Cascaded flavor id of the new flavor association"))
@utils.arg('region',
     metavar='<region>',
     help=_("Region name of the new flavor association"))
def do_flavor_association_create(cs, args):
    """Create a new flavor_association"""
    name="flavor"
    cs.associations.set_name(name)
    info = {
            "hflavor" : args.hflavor, 
            "flavor": args.flavor, 
            "region": args.region, 
            }
    f = cs.associations.create(**info)
    _print_association_list(name, [f])

###### image association 
def _print_association(association):
    info = association._info.copy()
    # ignore links, we don't need to present those
    
    utils.print_dict(info)

def _find_association(cs, association):
    """Get a association by name, ID."""
    try:
        return utils.find_resource(cs.associations, association)
    except exceptions.NotFound as e:
        raise e

def do_image_association_list(cs, args):
    """Print a list of available 'image_associations'."""
    name="image"
    cs.associations.set_name(name)
    association = cs.associations.list()
    _print_association_list(name, association)

@utils.arg('image_association',
    metavar='<image_association>',
    help=_("Name or ID of the image_association to delete"))
def do_image_association_delete(cs, args):
    """Delete a specific image_association"""
    name="image"
    cs.associations.set_name(name)
    association = _find_association(cs, args.image_association)
    cs.associations.delete(association)
    _print_association_list(name, [association])


@utils.arg('image_association',
     metavar='<image_association>',
     help=_("Name or ID of image_association"))
def do_image_association_show(cs, args):
    """Show details about the given image_association."""
    name="image"
    cs.associations.set_name(name)
    association = _find_association(cs, args.image_association)
    _print_association(association)

@utils.arg('id',
     metavar='<id>',
     help=_("Id of the image association"))
@utils.arg('--himage',
     metavar='<himage>',
     help=_("Cascading image id of the image association "))
@utils.arg('--image',
     metavar='<image>',
     help=_("Cascaded image id of the image association"))
@utils.arg('--region',
     metavar='<region>',
     help=_("Region name of the image association"))
def do_image_association_update(cs, args):
    """Update a image association"""
    name="image"
    cs.associations.set_name(name)
    f = cs.associations.update(args.id, himage=args.himage, image=args.image, 
                                region=args.region)
    _print_association_list(name, [f])

@utils.arg('himage',
     metavar='<himage>',
     help=_("Cascading image id of the new image association"))
@utils.arg('image',
     metavar='<image>',
     help=_("Cascaded image id of the new image association"))
@utils.arg('region',
     metavar='<region>',
     help=_("Region name of the new image association"))
def do_image_association_create(cs, args):
    """Create a new image_association"""
    name = "image"
    cs.associations.set_name(name)
    info = {
            "himage" : args.himage, 
            "image": args.image, 
            "region": args.region, 
            }
    f = cs.associations.create(**info)
    _print_association_list(name, [f])

###### network association 
def _print_association(association):
    info = association._info.copy()
    # ignore links, we don't need to present those
    
    utils.print_dict(info)

def _find_association(cs, association):
    """Get a association by name, ID."""
    try:
        return utils.find_resource(cs.associations, association)
    except exceptions.NotFound as e:
        raise e

def do_network_association_list(cs, args):
    """Print a list of available 'network_associations'."""
    name="network"
    cs.associations.set_name(name)
    association = cs.associations.list()
    _print_association_list(name, association)

@utils.arg('network_association',
    metavar='<network_association>',
    help=_("Name or ID of the network_association to delete"))
def do_network_association_delete(cs, args):
    """Delete a specific network_association"""
    name="network"
    cs.associations.set_name(name)
    association = _find_association(cs, args.network_association)
    cs.associations.delete(association)
    _print_association_list(name, [association])


@utils.arg('network_association',
     metavar='<network_association>',
     help=_("Name or ID of network_association"))
def do_network_association_show(cs, args):
    """Show details about the given network_association."""
    name="network"
    cs.associations.set_name(name)
    association = _find_association(cs, args.network_association)
    _print_association(association)

@utils.arg('id',
     metavar='<id>',
     help=_("Id of the network association"))
@utils.arg('--hnetwork',
     metavar='<hnetwork>',
     help=_("Cascading network id of the network association "))
@utils.arg('--network',
     metavar='<network>',
     help=_("Cascaded network id of the network association"))
@utils.arg('--region',
     metavar='<region>',
     help=_("Region name of the network association"))
def do_network_association_update(cs, args):
    """Update a network association"""
    name="network"
    cs.associations.set_name(name)
    f = cs.associations.update(args.id, hnetwork=args.hnetwork, network=args.network, 
                                region=args.region)
    _print_association_list(name, [f])

@utils.arg('hnetwork',
     metavar='<hnetwork>',
     help=_("Cascading network id of the new network association"))
@utils.arg('network',
     metavar='<network>',
     help=_("Cascaded network id of the new network association"))
@utils.arg('region',
     metavar='<region>',
     help=_("Region name of the new network association"))
def do_network_association_create(cs, args):
    """Create a new network_association"""
    name = "network"
    cs.associations.set_name(name)
    info = {
            "hnetwork" : args.hnetwork, 
            "network": args.network, 
            "region": args.region, 
            }
    f = cs.associations.create(**info)
    _print_association_list(name, [f])


def do_version_list(cs, args):
    """List all API versions."""
    result = cs.versions.list()
    columns = ["Id", "Status", "Updated"]
    utils.print_list(result, columns)

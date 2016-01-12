# -*- coding:utf-8 -*-

__author__ = 'q00222219@huawei'

import sys
import subprocess

_script_dir = "/home/fs_gateway/bin/"


def _add_dns_name(az, dc, postfix, cascaded_ip, fs_gateway):
    domain = ".".join([az, dc, postfix])

    az_dns = "/%s/%s" %(domain, cascaded_ip)

    compute_gw = "/gateway--compute.%s/%s" % (domain, fs_gateway)

    cinder_gw = "/gateway--volume.%s/%s" % (domain, fs_gateway)

    net_get = "/gateway--network.%s/%s" % (domain, fs_gateway)

    subprocess.call("cd %s;sh modify_dns_server_address.sh add %s" %
                    (_script_dir, az_dns), shell=True)

    subprocess.call("cd %s;sh modify_dns_server_address.sh add %s" %
                    (_script_dir, compute_gw), shell=True)

    subprocess.call("cd %s;sh modify_dns_server_address.sh add %s" %
                    (_script_dir, cinder_gw), shell=True)

    subprocess.call("cd %s;sh modify_dns_server_address.sh add %s" %
                    (_script_dir,net_get), shell=True)


def _remove_dns_name(az, dc, postfix, cascaded_ip, fs_gateway):
    domain = ".".join([az, dc, postfix])

    az_dns = "/%s/%s" %(domain, cascaded_ip)

    compute_gw = "/gateway--compute.%s/%s" % (domain, fs_gateway)

    cinder_gw = "/gateway--volume.%s/%s" % (domain, fs_gateway)

    net_get = "/gateway--network.%s/%s" % (domain, fs_gateway)

    subprocess.call("cd %s;sh modify_dns_server_address.sh remove %s" %
                    (_script_dir, az_dns), shell=True)

    subprocess.call("cd %s;sh modify_dns_server_address.sh remove %s" %
                    (_script_dir, compute_gw), shell=True)

    subprocess.call("cd %s;sh modify_dns_server_address.sh remove %s" %
                    (_script_dir, cinder_gw), shell=True)

    subprocess.call("cd %s;sh modify_dns_server_address.sh remove %s" %
                    (_script_dir, net_get),shell=True)


def _register_keystone_endpoint(az, dc, postfix, v2v_gateway):
    subprocess.call("cd %s;sh create_keystone_endpoint.sh %s %s %s %s" %
                    (_script_dir, az, dc, postfix, v2v_gateway), shell=True)


def _unregister_keystone_endpoint(az, dc, postfix):
    subprocess.call("cd %s;sh remove_keystone_endpoint.sh %s %s %s" %
                    (_script_dir, az, dc, postfix), shell=True)


def _modify_proxy_config(az, dc, postfix, proxy_host_id, proxy):
    subprocess.call("cd %s;sh modify_proxy.sh %s %s %s %s %s" %
                    (_script_dir, az, dc, postfix, proxy_host_id, proxy),
                    shell=True)


def _remove_proxy(proxy_host_id, proxy):
    subprocess.call("cd %s;sh remove_proxy.sh %s %s" %
                    (_script_dir, proxy_host_id, proxy),
                    shell=True)


def register_availability_zone(az, dc, postfix, cascaded_ip,
                               proxy_host_id, proxy, fs_gateway, v2v_gateway):
    _add_dns_name(az, dc, postfix, cascaded_ip, fs_gateway)
    _register_keystone_endpoint(az, dc, postfix, v2v_gateway)
    _modify_proxy_config(az, dc, postfix, proxy_host_id, proxy)


def unregister_availability_zone(az, dc, postfix, cascaded_ip,
                                 proxy_host_id, proxy, fs_gateway):
    _remove_dns_name(az, dc, postfix, cascaded_ip, fs_gateway)
    _unregister_keystone_endpoint(az, dc, postfix)
    _remove_proxy(proxy_host_id, proxy)


if __name__ == '__main__':
    act = sys.argv[1]

    if act == "--register":
        cascaded_domain = sys.argv[2]
        cascaded_ip = sys.argv[3]
        proxy_host_id = sys.argv[4]
        proxy = sys.argv[5]
        fs_gateway = sys.argv[6]
        v2v_gateway = sys.argv[7]

        cascaded_domain_splits = cascaded_domain.split(".")
        az = cascaded_domain_splits[0]
        dc = cascaded_domain_splits[1]
        postfix = ".".join(cascaded_domain_splits[2:])

        register_availability_zone(az, dc, postfix, cascaded_ip,
                                   proxy_host_id, proxy,
                                   fs_gateway, v2v_gateway)

    elif act == "--unregister":
        cascaded_domain = sys.argv[2]
        cascaded_ip = sys.argv[3]
        proxy_host_id = sys.argv[4]
        proxy = sys.argv[5]
        fs_gateway = sys.argv[6]
        v2v_gateway = sys.argv[7]

        cascaded_domain_splits = cascaded_domain.split(".")
        az = cascaded_domain_splits[0]
        dc = cascaded_domain_splits[1]
        postfix = ".".join(cascaded_domain_splits[2:])

        unregister_availability_zone(az, dc, postfix, cascaded_ip,
                                     proxy_host_id, proxy, fs_gateway)

    elif act == "--help":
        print "use:python /usr/bin/fs_gateway_register " \
              "[--register/unregister] cascaded_domain cascaded_ip " \
              "proxy_host_id proxy_num fs_gateway v2v_gateway"

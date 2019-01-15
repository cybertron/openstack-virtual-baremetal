#!/usr/bin/env python
# Copyright 2015 Red Hat Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import argparse
import json
import os
import yaml

import os_client_config


def _parse_args():
    parser = argparse.ArgumentParser(
        prog='build-nodes-json.py',
        description='Tool for collecting virtual IPMI details',
    )
    parser.add_argument('--env', '-e',
                        dest='env',
                        default=None,
                        help='YAML file containing OVB environment details')
    parser.add_argument('--bmc_prefix',
                        dest='bmc_prefix',
                        default='bmc',
                        help='BMC name prefix')
    parser.add_argument('--baremetal_prefix',
                        dest='baremetal_prefix',
                        default='baremetal',
                        help='Baremetal name prefix')
    parser.add_argument('--private_net',
                        dest='private_net',
                        default='private',
                        help='DEPRECATED: This parameter is ignored.')
    parser.add_argument('--provision_net',
                        dest='provision_net',
                        default='provision',
                        help='DEPRECATED: This parameter is ignored.')
    parser.add_argument('--nodes_json',
                        dest='nodes_json',
                        default='nodes.json',
                        help='Destination to store the nodes json file to')
    parser.add_argument('--add_undercloud',
                        dest='add_undercloud',
                        action='store_true',
                        help='DEPRECATED: Use --network_details instead. '
                             'Adds the undercloud details to the json file.')
    parser.add_argument('--network_details',
                        dest='network_details',
                        action='store_true',
                        help='Include addresses for all nodes on all networks '
                             'in a network_details key')
    # TODO(dtantsur): change the default to ipmi when Ocata is not supported
    parser.add_argument('--driver', default='pxe_ipmitool',
                        help='Bare metal driver to use')
    parser.add_argument('--physical_network',
                        action='store_true',
                        help='Set the physical network attribute of baremetal '
                             'ports. (Requires Rocky or later Ironic)')
    args = parser.parse_args()
    return args


def _get_names(args):
    if args.env is None:
        bmc_base = args.bmc_prefix
        baremetal_base = args.baremetal_prefix
        # FIXME: This is not necessarily true.
        undercloud_name = 'undercloud'
    else:
        with open(args.env) as f:
            e = yaml.safe_load(f)
        bmc_base = e['parameter_defaults']['bmc_prefix']
        baremetal_base = e['parameter_defaults']['baremetal_prefix']
        role = e.get('parameter_defaults', {}).get('role')
        if role and baremetal_base.endswith('-' + role):
            baremetal_base = baremetal_base[:-len(role) - 1]
        undercloud_name = e.get('parameter_defaults', {}).get('undercloud_name')  # noqa: E501
    return bmc_base, baremetal_base, undercloud_name


def _get_clients():
    cloud = os.environ.get('OS_CLOUD')
    nova = os_client_config.make_client('compute', cloud=cloud)
    neutron = os_client_config.make_client('network', cloud=cloud)
    glance = os_client_config.make_client('image', cloud=cloud)
    return nova, neutron, glance


def _get_ports(neutron, bmc_base, baremetal_base):
    all_ports = sorted(neutron.list_ports()['ports'], key=lambda x: x['name'])
    bmc_ports = list([p for p in all_ports
                     if p['name'].startswith(bmc_base)])
    bm_ports = list([p for p in all_ports
                    if p['name'].startswith(baremetal_base)])
    if len(bmc_ports) != len(bm_ports):
        raise RuntimeError('Found different numbers of baremetal and '
                           'bmc ports. bmc: %s baremetal: %s' % (bmc_ports,
                                                                 bm_ports))
    provision_net_map = {}
    for port in bm_ports:
        provision_net_map.update({
            port.get('id'):
                neutron.list_subnets(
                    id=port['fixed_ips'][0]['subnet_id'])['subnets'][0].get(
                    'name')})
    return bmc_ports, bm_ports, provision_net_map


def _build_nodes(nova, glance, bmc_ports, bm_ports, provision_net_map,
                 baremetal_base, undercloud_name, driver, physical_network):
    node_template = {
        'pm_type': driver,
        'mac': '',
        'cpu': '',
        'memory': '',
        'disk': '',
        'arch': 'x86_64',
        'pm_user': 'admin',
        'pm_password': 'password',
        'pm_addr': '',
        'capabilities': 'boot_option:local',
        'name': '',
    }
    if physical_network:
        node_template.pop('mac')
    nodes = []
    cache = {}
    network_details = {}
    for bmc_port, baremetal_port in zip(bmc_ports, bm_ports):
        baremetal = nova.servers.get(baremetal_port['device_id'])
        network_details[baremetal.name] = {}
        network_details[baremetal.name]['id'] = baremetal.id
        network_details[baremetal.name]['ips'] = baremetal.addresses
        node = dict(node_template)
        node['pm_addr'] = bmc_port['fixed_ips'][0]['ip_address']
        provision_net = provision_net_map.get(baremetal_port['id'])
        mac = baremetal.addresses[provision_net][0]['OS-EXT-IPS-MAC:mac_addr']
        if physical_network:
            node.update({'ports': [{'address': mac,
                                    'physical_network': provision_net}]})
        else:
            node['mac'] = [mac]
        if not cache.get(baremetal.flavor['id']):
            cache[baremetal.flavor['id']] = nova.flavors.get(
                baremetal.flavor['id'])
        flavor = cache.get(baremetal.flavor['id'])
        node['cpu'] = flavor.vcpus
        node['memory'] = flavor.ram
        node['disk'] = flavor.disk
        # NOTE(bnemec): Older versions of Ironic won't allow _ characters in
        # node names, so translate to the allowed character -
        node['name'] = baremetal.name.replace('_', '-')

        # If a node has uefi firmware ironic needs to be aware of this, in nova
        # this is set using a image property called "hw_firmware_type"
        # NOTE(bnemec): Boot from volume does not have an image associated with
        # the instance so we can't do this.
        if baremetal.image:
            if not cache.get(baremetal.image['id']):
                cache[baremetal.image['id']] = glance.images.get(
                    baremetal.image['id'])
            image = cache.get(baremetal.image['id'])
            if image.get('hw_firmware_type') == 'uefi':
                node['capabilities'] += ",boot_mode:uefi"
        else:
            # With boot from volume the flavor disk size doesn't matter.  We
            # need to look up the volume disk size.
            cloud = os.environ.get('OS_CLOUD')
            cinder = os_client_config.make_client('volume', cloud=cloud)
            vol_id = baremetal.to_dict()[
                'os-extended-volumes:volumes_attached'][0]['id']
            volume = cinder.volumes.get(vol_id)
            node['disk'] = volume.size

        bm_name_end = baremetal.name[len(baremetal_base):]
        if '-' in bm_name_end:
            profile = bm_name_end[1:].split('_')[0]
            node['capabilities'] += ',profile:%s' % profile

        nodes.append(node)

    extra_nodes = []

    if undercloud_name:
        undercloud_node_template = {
            'name': undercloud_name,
            'id': '',
            'ips': [],
        }
        try:
            undercloud_instance = nova.servers.list(
                search_opts={'name': undercloud_name})[0]
        except IndexError:
            print('Undercloud %s specified in the environment file is not '
                  'available in nova. No undercloud details will be '
                  'included in the output.' % undercloud_name)
        else:
            undercloud_node_template['id'] = undercloud_instance.id
            undercloud_node_template['ips'] = nova.servers.ips(
                undercloud_instance)

            extra_nodes.append(undercloud_node_template)
            network_details[undercloud_name] = dict(
                id=undercloud_instance.id,
                ips=undercloud_instance.addresses)
    return nodes, extra_nodes, network_details


def _write_nodes(nodes, extra_nodes, network_details, args):
    with open(args.nodes_json, 'w') as node_file:
        resulting_json = {'nodes': nodes}
        if args.add_undercloud and extra_nodes:
            resulting_json['extra_nodes'] = extra_nodes
        if args.network_details:
            resulting_json['network_details'] = network_details
        contents = json.dumps(resulting_json, indent=2)
        node_file.write(contents)
        print(contents)
        print('Wrote node definitions to %s' % args.nodes_json)


def _get_node_profile(node):
    parts = node['capabilities'].split(',')
    for p in parts:
        if p.startswith('profile'):
            return p.split(':')[-1]
    return ''


def _write_role_nodes(nodes, args):
    by_profile = {}
    for n in nodes:
        by_profile.setdefault(_get_node_profile(n), []).append(n)
    # Don't write role-specific files if no roles were used.
    if len(by_profile) == 1 and list(by_profile.keys())[0] == '':
        return
    for profile, profile_nodes in by_profile.items():
        filepart = profile
        if not profile:
            filepart = 'no-profile'
        outfile = '%s-%s.json' % (os.path.splitext(args.nodes_json)[0],
                                  filepart)
        with open(outfile, 'w') as f:
            contents = json.dumps({'nodes': profile_nodes}, indent=2)
            f.write(contents)
            print(contents)
            print('Wrote profile "%s" node definitions to %s' %
                  (profile, outfile))


def main():
    args = _parse_args()
    bmc_base, baremetal_base, undercloud_name = _get_names(args)
    nova, neutron, glance = _get_clients()
    bmc_ports, bm_ports, provision_net_map = _get_ports(neutron, bmc_base,
                                                        baremetal_base)
    (nodes,
     extra_nodes,
     network_details) = _build_nodes(nova, glance, bmc_ports, bm_ports,
                                     provision_net_map, baremetal_base,
                                     undercloud_name, args.driver,
                                     args.physical_network)
    _write_nodes(nodes, extra_nodes, network_details, args)
    _write_role_nodes(nodes, args)


if __name__ == '__main__':
    main()

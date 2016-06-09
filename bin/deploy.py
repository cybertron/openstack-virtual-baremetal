#!/usr/bin/env python
# Copyright 2016 Red Hat Inc.
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
import os
import random
import yaml

from heatclient import client as heat_client
from heatclient.common import template_utils
from keystoneclient.v2_0 import client as keystone_client

def _parse_args():
    parser = argparse.ArgumentParser(description='Deploy an OVB environment')
    parser.add_argument('--env',
                        help='Path to Heat environment file describing the OVB '
                             'environment to be deployed.',
                        default='env.yaml')
    parser.add_argument('--id',
                        help='Identifier to add to all resource names. The '
                             'resulting names will look like undercloud-ID or '
                             'baremetal-ID. By default no changes will be made to '
                             'the resource names. If an id is specified, a new '
                             'environment file will be written to env-ID.yaml. ')
    parser.add_argument('--name',
                        help='Name for the Heat stack to be created.')
    parser.add_argument('--quintupleo',
                        help='Deploy a full environment suitable for TripleO '
                             'development.',
                        action='store_true',
                        default=False)
    return parser.parse_args()

def _process_args(args):
    if args.id and not args.quintupleo:
        raise RuntimeError('--id requires --quintupleo')

    env_path = args.env
    if args.name:
        stack_name = args.name
    else:
        stack_name = 'baremetal'
        if args.quintupleo:
            stack_name = 'quintupleo'
    if not args.quintupleo:
        stack_template = 'templates/virtual-baremetal.yaml'
    else:
        stack_template = 'templates/quintupleo.yaml'
    return stack_name, stack_template

def _add_identifier(env_data, name, identifier, default=None, parameter=True):
    param_key = 'parameters'
    if not parameter:
        param_key = 'parameter_defaults'
    if param_key not in env_data or not env_data[param_key]:
        env_data[param_key] = {}
    original = env_data[param_key].get(name)
    if original is None:
        original = default
    if original is None:
        raise RuntimeError('No base value found when adding id')
    env_data[param_key][name] = '%s-%s' % (original, identifier)

def _generate_id_env(args):
    with open(args.env) as f:
        env_data = yaml.safe_load(f)
    _add_identifier(env_data, 'provision_net', args.id, default='provision')
    _add_identifier(env_data, 'public_net', args.id, default='public')
    _add_identifier(env_data, 'baremetal_prefix', args.id, default='baremetal')
    _add_identifier(env_data, 'bmc_prefix', args.id, default='bmc')
    _add_identifier(env_data, 'undercloud_name', args.id, default='undercloud')
    _add_identifier(env_data, 'overcloud_internal_net', args.id,
                    default='internal', parameter=False)
    _add_identifier(env_data, 'overcloud_storage_net', args.id,
                    default='storage', parameter=False)
    _add_identifier(env_data, 'overcloud_storage_mgmt_net', args.id,
                    default='storage_mgmt', parameter=False)
    _add_identifier(env_data, 'overcloud_tenant_net', args.id,
                    default='tenant', parameter=False)
    env_path = 'env-%s.yaml' % args.id
    with open(env_path, 'w') as f:
        yaml.safe_dump(env_data, f, default_flow_style=False)
    return env_path

def _get_heat_client():
    cloud = os.environ.get('OS_CLOUD')
    if cloud:
        import os_client_config
        return os_client_config.make_client('orchestration', cloud=cloud)
    else:
        username = os.environ.get('OS_USERNAME')
        password = os.environ.get('OS_PASSWORD')
        tenant = os.environ.get('OS_TENANT_NAME')
        auth_url = os.environ.get('OS_AUTH_URL')
        if not username or not password or not tenant or not auth_url:
            print('Source an appropriate rc file first')
            sys.exit(1)

        # Get token for Heat to use
        kclient = keystone_client.Client(username=username, password=password,
                                        tenant_name=tenant, auth_url=auth_url)
        token_data = kclient.get_raw_token_from_identity_service(
            username=username,
            password=password,
            tenant_name=tenant,
            auth_url=auth_url)
        token_id = token_data['token']['id']
        # Get Heat endpoint
        for endpoint in token_data['serviceCatalog']:
            if endpoint['name'] == 'heat':
                # TODO: What if there's more than one endpoint?
                heat_endpoint = endpoint['endpoints'][0]['publicURL']

        return heat_client.Client('1', endpoint=heat_endpoint, token=token_id)

def _deploy(stack_name, stack_template, env_path):
    hclient = _get_heat_client()

    template_files, template = template_utils.get_template_contents(
        stack_template)
    env_files, env = template_utils.process_multiple_environments_and_files(
        ['templates/resource-registry.yaml', env_path])
    all_files = {}
    all_files.update(template_files)
    all_files.update(env_files)

    hclient.stacks.create(stack_name=stack_name,
                          template=template,
                          environment=env,
                          files=all_files)

    print 'Deployment of stack "%s" started.' % stack_name

if __name__ == '__main__':
    args = _parse_args()
    env_path = args.env
    stack_name, stack_template = _process_args(args)
    if args.id:
        env_path = _generate_id_env(args)
    _deploy(stack_name, stack_template, env_path)

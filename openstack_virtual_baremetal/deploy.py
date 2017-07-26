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
import sys
import time
import yaml

from heatclient import client as heat_client
from heatclient.common import template_utils
import os_client_config

import auth

def _parse_args():
    parser = argparse.ArgumentParser(description='Deploy an OVB environment')
    parser.add_argument('--env',
                        help='Path to Heat environment file describing the OVB '
                             'environment to be deployed. Default: %(default)s',
                        default='env.yaml')
    parser.add_argument('--id',
                        help='Identifier to add to all resource names. The '
                             'resulting names will look like undercloud-ID or '
                             'baremetal-ID. By default no changes will be made to '
                             'the resource names. If an id is specified, a new '
                             'environment file will be written to env-ID.yaml. ')
    parser.add_argument('--name',
                        help='Name for the Heat stack to be created. Defaults '
                             'to "baremetal" in a standard deployment. If '
                             '--quintupleo is specified then the default is '
                             '"quintupleo".')
    parser.add_argument('--quintupleo',
                        help='Deploy a full environment suitable for TripleO '
                             'development.',
                        action='store_true',
                        default=False)
    parser.add_argument('--role',
                        help='Additional environment file describing a '
                             'secondary role to be deployed alongside the '
                             'primary one described in the main environment.',
                        action='append',
                        default=[])
    parser.add_argument('--poll',
                        help='Poll until the Heat stack(s) are complete. '
                             'Automatically enabled when multiple roles are '
                             'deployed.',
                        action='store_true',
                        default=False)
    return parser.parse_args()

def _process_args(args):
    if args.id and not args.quintupleo:
        raise RuntimeError('--id requires --quintupleo')
    if args.role and not args.quintupleo:
        raise RuntimeError('--role requires --quintupleo')

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
    # parameter_defaults may exist, but be None, so we need to handle that case
    parameter_defaults = env_data.get('parameter_defaults')
    if not parameter_defaults:
        parameter_defaults = {}
    role = parameter_defaults.get('role')
    if role is not None:
        env_data['parameters']['baremetal_prefix'] += '-' + role
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

def _validate_env(args, env_path):
    """Check for invalid environment configurations

    :param args: Argparse args.
    :param env_path: Path of the environment file to validate.
    """
    if not args.id:
        with open(env_path) as f:
            env_data = yaml.safe_load(f)
        role = env_data.get('parameter_defaults', {}).get('role')
        if (role and
                env_data['parameters']['baremetal_prefix'].endswith('-' +
                                                                    role)):
            raise RuntimeError('baremetal_prefix ends with role name.  This '
                               'will break build-nodes-json.  Please choose a '
                               'different baremetal_prefix or role name.')

def _get_heat_client():
    return os_client_config.make_client('orchestration',
                                        cloud=auth.OS_CLOUD)

def _deploy(stack_name, stack_template, env_path, poll):
    hclient = _get_heat_client()

    template_files, template = template_utils.get_template_contents(
        stack_template)
    env_files, env = template_utils.process_multiple_environments_and_files(
        ['templates/resource-registry.yaml', env_path])
    all_files = {}
    all_files.update(template_files)
    all_files.update(env_files)
    parameters = auth._create_auth_parameters()

    hclient.stacks.create(stack_name=stack_name,
                          template=template,
                          environment=env,
                          files=all_files,
                          parameters=parameters)

    print 'Deployment of stack "%s" started.' % stack_name
    if poll:
        _poll_stack(stack_name, hclient)

def _poll_stack(stack_name,  hclient):
    """Poll status for stack_name until it completes or fails"""
    print 'Waiting for stack to complete',
    done = False
    while not done:
        print '.',
        stack = hclient.stacks.get(stack_name, resolve_outputs=False)
        sys.stdout.flush()
        if stack.status == 'COMPLETE':
            print 'Stack %s created successfully' % stack_name
            done = True
        elif stack.status == 'FAILED':
            raise RuntimeError('Failed to create stack %s' % stack_name)
        else:
            time.sleep(10)

# Abstract out the role file interactions for easier unit testing
def _load_role_data(base_env, role_file, args):
    with open(base_env) as f:
        base_data = yaml.safe_load(f)
    with open(role_file) as f:
        role_data = yaml.safe_load(f)
    with open(args.env) as f:
        orig_data = yaml.safe_load(f)
    return base_data, role_data, orig_data

def _write_role_file(role_env, role_file):
    with open(role_file, 'w') as f:
        yaml.safe_dump(role_env, f, default_flow_style=False)

def _process_role(role_file, base_env, stack_name, args):
    """Merge a partial role env with the base env

    :param role: Filename of an environment file containing the definition
        of the role.
    :param base_env: Filename of the environment file used to deploy the
        stack containing shared resources such as the undercloud and
        networks.
    :param stack_name: Name of the stack deployed using base_env.
    :param args: The command-line arguments object from argparse.
    """
    base_data, role_data, orig_data = _load_role_data(base_env, role_file,
                                                      args)
    inherited_keys = ['baremetal_image', 'bmc_flavor', 'bmc_image',
                      'external_net', 'key_name', 'os_auth_url',
                      'os_password', 'os_tenant', 'os_user',
                      'private_net', 'provision_net', 'public_net',
                      'overcloud_internal_net', 'overcloud_storage_mgmt_net',
                      'overcloud_storage_net','overcloud_tenant_net',
                      ]
    allowed_registry_keys = ['OS::OVB::BaremetalPorts']
    role_env = role_data
    # resource_registry is intentionally omitted as it should not be inherited
    for section in ['parameters', 'parameter_defaults']:
        role_env[section].update({
            k: v for k, v in base_data.get(section, {}).items()
            if k in inherited_keys})
    # Most of the resource_registry should not be included in role envs.
    # Only allow specific entries that may be needed.
    role_env['resource_registry'] = {
        k: v for k, v in role_env.get('resource_registry', {}).items()
        if k in allowed_registry_keys}
    # We need to start with the unmodified prefix
    base_prefix = orig_data['parameters']['baremetal_prefix']
    # But we do need to add the id if one is in use
    if args.id:
        base_prefix += '-%s' % args.id
    bmc_prefix = base_data['parameters']['bmc_prefix']
    role = role_data['parameter_defaults']['role']
    role_env['parameters']['baremetal_prefix'] = '%s-%s' % (base_prefix, role)
    role_env['parameters']['bmc_prefix'] = '%s-%s' % (bmc_prefix, role)
    role_file = 'env-%s-%s.yaml' % (stack_name, role)
    _write_role_file(role_env, role_file)
    return role_file, role

def _deploy_roles(stack_name, args, env_path):
    for r in args.role:
        role_env, role_name = _process_role(r, env_path, stack_name, args)
        _deploy(stack_name + '-%s' % role_name,
                'templates/virtual-baremetal.yaml',
                role_env, poll=True)

if __name__ == '__main__':
    args = _parse_args()
    env_path = args.env
    stack_name, stack_template = _process_args(args)
    if args.id:
        env_path = _generate_id_env(args)
    _validate_env(args, env_path)
    poll = args.poll
    if args.role:
        poll = True
    _deploy(stack_name, stack_template, env_path, poll=poll)
    _deploy_roles(stack_name, args, env_path)

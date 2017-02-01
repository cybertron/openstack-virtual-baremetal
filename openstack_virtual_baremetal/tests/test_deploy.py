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

import io
import unittest
import yaml

import mock

import deploy

class TestProcessArgs(unittest.TestCase):
    def test_basic(self):
        mock_args = mock.Mock()
        mock_args.name = None
        mock_args.quintupleo = False
        mock_args.id = None
        mock_args.role = []
        name, template = deploy._process_args(mock_args)
        self.assertEqual('baremetal', name)
        self.assertEqual('templates/virtual-baremetal.yaml', template)

    def test_name(self):
        mock_args = mock.Mock()
        mock_args.name = 'foo'
        mock_args.quintupleo = False
        mock_args.id = None
        mock_args.role = []
        name, template = deploy._process_args(mock_args)
        self.assertEqual('foo', name)
        self.assertEqual('templates/virtual-baremetal.yaml', template)

    def test_quintupleo(self):
        mock_args = mock.Mock()
        mock_args.name = None
        mock_args.quintupleo = True
        name, template = deploy._process_args(mock_args)
        self.assertEqual('quintupleo', name)
        self.assertEqual('templates/quintupleo.yaml', template)

    def test_quintupleo_name(self):
        mock_args = mock.Mock()
        mock_args.name = 'foo'
        mock_args.quintupleo = True
        name, template = deploy._process_args(mock_args)
        self.assertEqual('foo', name)
        self.assertEqual('templates/quintupleo.yaml', template)

    def test_id_quintuple(self):
        mock_args = mock.Mock()
        mock_args.id = 'foo'
        mock_args.quintupleo = False
        self.assertRaises(RuntimeError, deploy._process_args, mock_args)


test_env = u"""parameters:
  provision_net: provision
  public_net: public
  baremetal_prefix: baremetal
  bmc_prefix: bmc
  os_user: admin
"""
test_env_output = {
    'parameter_defaults':
        {'overcloud_internal_net': 'internal-foo',
         'overcloud_storage_net': 'storage-foo',
         'overcloud_storage_mgmt_net': 'storage_mgmt-foo',
         'overcloud_tenant_net': 'tenant-foo'},
    'parameters':
        {'baremetal_prefix': 'baremetal-foo',
         'undercloud_name': 'undercloud-foo',
         'provision_net': 'provision-foo',
         'public_net': 'public-foo',
         'bmc_prefix': 'bmc-foo',
         'os_user': 'admin'}
    }


class TestIdEnv(unittest.TestCase):
    def test_add_identifier(self):
        env_data = {'parameters': {'foo': 'bar'}}
        deploy._add_identifier(env_data, 'foo', 'baz')
        self.assertEqual('bar-baz', env_data['parameters']['foo'])

    def test_add_identifier_defaults(self):
        env_data = {'parameter_defaults': {'foo': 'bar'}}
        deploy._add_identifier(env_data, 'foo', 'baz', parameter=False)
        self.assertEqual('bar-baz', env_data['parameter_defaults']['foo'])

    @mock.patch('yaml.safe_dump')
    def test_generate(self, mock_safe_dump):
        mock_args = mock.Mock()
        mock_args.id = 'foo'
        with mock.patch('deploy.open',
                        mock.mock_open(read_data=test_env),
                        create=True) as mock_open:
            path = deploy._generate_id_env(mock_args)
            self.assertEqual('env-foo.yaml', path)
            mock_safe_dump.assert_called_once_with(test_env_output, mock.ANY,
                                                   default_flow_style=False)

    @mock.patch('yaml.safe_dump')
    def test_generate_undercloud_name(self, mock_safe_dump):
        mock_args = mock.Mock()
        mock_args.id = 'foo'
        env = test_env + '  undercloud_name: undercloud\n'
        env_output = dict(test_env_output)
        env_output['parameters']['undercloud_name'] = 'undercloud-foo'
        with mock.patch('deploy.open',
                        mock.mock_open(read_data=env),
                        create=True) as mock_open:
            path = deploy._generate_id_env(mock_args)
            self.assertEqual('env-foo.yaml', path)
            mock_safe_dump.assert_called_once_with(env_output, mock.ANY,
                                                   default_flow_style=False)

# _process_role test data
role_base_data = {
    'parameter_defaults': {
        'overcloud_storage_mgmt_net': 'storage_mgmt-foo',
        'overcloud_internal_net': 'internal-foo',
        'overcloud_storage_net': 'storage-foo',
        'role': 'control',
        'overcloud_tenant_net': 'tenant-foo'
        },
    'parameters': {
        'os_user': 'admin',
        'key_name': 'default',
        'undercloud_name': 'undercloud-foo',
        'bmc_image': 'bmc-base',
        'baremetal_flavor': 'baremetal',
        'os_auth_url': 'http://1.1.1.1:5000/v2.0',
        'provision_net': 'provision-foo',
        'os_password': 'password',
        'os_tenant': 'admin',
        'bmc_prefix': 'bmc-foo',
        'public_net': 'public-foo',
        'undercloud_image': 'centos7-base',
        'baremetal_image': 'ipxe-boot',
        'external_net': 'external',
        'private_net': 'private',
        'baremetal_prefix': 'baremetal-foo-control',
        'undercloud_flavor': 'undercloud-16',
        'node_count': 3,
        'bmc_flavor': 'bmc'
        },
    'resource_registry': {
        'OS::OVB::BaremetalNetworks': 'templates/baremetal-networks-all.yaml',
        'OS::OVB::BaremetalPorts': 'templates/baremetal-ports-public-bond.yaml'
        }
    }
role_specific_data = {
    'parameter_defaults': {
        'role': 'compute',
        },
    'parameters': {
        'key_name': 'default',
        'baremetal_flavor': 'baremetal',
        'bmc_image': 'bmc-base',
        'bmc_prefix': 'bmc',
        'node_count': 2,
        'bmc_flavor': 'bmc'
        },
    'resource_registry': {
        'OS::OVB::BaremetalNetworks': 'templates/baremetal-networks-all.yaml',
        'OS::OVB::BaremetalPorts': 'templates/baremetal-ports-all.yaml'
        }
    }
role_original_data = {
    'parameter_defaults': {
        'role': 'control',
        },
    'parameters': {
        'os_user': 'admin',
        'key_name': 'default',
        'undercloud_name': 'undercloud',
        'baremetal_flavor': 'baremetal',
        'os_auth_url': 'http://1.1.1.1:5000/v2.0',
        'provision_net': 'provision',
        'bmc_image': 'bmc-base',
        'os_tenant': 'admin',
        'bmc_prefix': 'bmc',
        'public_net': 'public',
        'undercloud_image': 'centos7-base',
        'baremetal_image': 'ipxe-boot',
        'external_net': 'external',
        'os_password': 'password',
        'private_net': 'private',
        'baremetal_prefix': 'baremetal',
        'undercloud_flavor': 'undercloud-16',
        'node_count': 3,
        'bmc_flavor': 'bmc'
        },
    'resource_registry': {
        'OS::OVB::BaremetalNetworks': 'templates/baremetal-networks-all.yaml',
        'OS::OVB::BaremetalPorts': 'templates/baremetal-ports-public-bond.yaml'
        }
    }
# end _process_role test data

class TestDeploy(unittest.TestCase):
    def _test_deploy(self, mock_ghc, mock_tu, mock_poll, poll=False):
        mock_client = mock.Mock()
        mock_ghc.return_value = mock_client
        template_files = {'template.yaml': {'foo': 'bar'}}
        template = {'foo': 'bar'}
        mock_tu.get_template_contents.return_value = (
            template_files, template
            )
        env_files = {'templates/resource_registry.yaml': {'bar': 'baz'},
                     'env.yaml': {'parameters': {}}}
        env = {'parameters': {}}
        mock_tu.process_multiple_environments_and_files.return_value = (
            env_files, env
            )
        all_files = {}
        all_files.update(template_files)
        all_files.update(env_files)
        deploy._deploy('test', 'template.yaml', 'env.yaml', poll)
        mock_tu.get_template_contents.assert_called_once_with('template.yaml')
        process = mock_tu.process_multiple_environments_and_files
        process.assert_called_once_with(['templates/resource-registry.yaml',
                                         'env.yaml'])
        mock_client.stacks.create.assert_called_once_with(stack_name='test',
                                                          template=template,
                                                          environment=env,
                                                          files=all_files)
        if not poll:
            mock_poll.assert_not_called()
        else:
            mock_poll.assert_called_once_with('test', mock_client)

    @mock.patch('deploy._poll_stack')
    @mock.patch('deploy.template_utils')
    @mock.patch('deploy._get_heat_client')
    def test_deploy(self, mock_ghc, mock_tu, mock_poll):
        self._test_deploy(mock_ghc, mock_tu, mock_poll)

    @mock.patch('deploy._poll_stack')
    @mock.patch('deploy.template_utils')
    @mock.patch('deploy._get_heat_client')
    def test_deploy_poll(self, mock_ghc, mock_tu, mock_poll):
        self._test_deploy(mock_ghc, mock_tu, mock_poll, True)

    @mock.patch('time.sleep')
    def test_poll(self, mock_sleep):
        hclient = mock.Mock()
        stacks = [mock.Mock(), mock.Mock()]
        stacks[0].status = 'IN_PROGRESS'
        stacks[1].status = 'COMPLETE'
        hclient.stacks.get.side_effect = stacks
        deploy._poll_stack('foo', hclient)
        self.assertEqual([mock.call('foo', resolve_outputs=False),
                          mock.call('foo', resolve_outputs=False)],
                          hclient.stacks.get.mock_calls)

    @mock.patch('time.sleep')
    def test_poll_fail(self, mock_sleep):
        hclient = mock.Mock()
        stacks = [mock.Mock(), mock.Mock()]
        stacks[0].status = 'IN_PROGRESS'
        stacks[1].status = 'FAILED'
        hclient.stacks.get.side_effect = stacks
        self.assertRaises(RuntimeError, deploy._poll_stack, 'foo', hclient)
        self.assertEqual([mock.call('foo', resolve_outputs=False),
                          mock.call('foo', resolve_outputs=False)],
                          hclient.stacks.get.mock_calls)

    @mock.patch('deploy._write_role_file')
    @mock.patch('deploy._load_role_data')
    def test_process_role(self, mock_load, mock_write):
        mock_load.return_value = (role_base_data, role_specific_data,
                                  role_original_data)
        args = mock.Mock()
        args.id = 'foo'
        role_file, role = deploy._process_role('foo-compute.yaml', 'foo.yaml',
                                               'foo', args)
        mock_load.assert_called_once_with('foo.yaml', 'foo-compute.yaml', args)
        self.assertEqual('env-foo-compute.yaml', role_file)
        self.assertEqual('compute', role)
        output = mock_write.call_args[0][0]
        # These values are computed in _process_role
        self.assertEqual('baremetal-foo-compute',
                         output['parameters']['baremetal_prefix'])
        self.assertEqual('bmc-foo-compute',
                         output['parameters']['bmc_prefix'])
        # These should be inherited
        self.assertEqual('ipxe-boot', output['parameters']['baremetal_image'])
        self.assertEqual('tenant-foo',
                         output['parameter_defaults']['overcloud_tenant_net'])
        # This should not be present in a role env, even if set in the file
        self.assertNotIn('OS::OVB::BaremetalNetworks',
                         output['resource_registry'])
        # This should be the value set in the role env, not the base one
        self.assertEqual('templates/baremetal-ports-all.yaml',
                         output['resource_registry']['OS::OVB::BaremetalPorts'])

    @mock.patch('deploy._deploy')
    @mock.patch('deploy._process_role')
    def test_deploy_roles(self, mock_process, mock_deploy):
        args = mock.Mock()
        args.role = ['foo-compute.yaml']
        mock_process.return_value = ('env-foo-compute.yaml', 'compute')
        deploy._deploy_roles('foo', args, 'foo.yaml')
        mock_process.assert_called_once_with('foo-compute.yaml', 'foo.yaml',
                                             'foo', args)
        mock_deploy.assert_called_once_with('foo-compute',
                                            'templates/virtual-baremetal.yaml',
                                            'env-foo-compute.yaml',
                                            poll=True)

    @mock.patch('deploy._process_role')
    def test_deploy_roles_empty(self, mock_process):
        args = mock.Mock()
        args.role = []
        deploy._deploy_roles('foo', args, 'foo.yaml')
        mock_process.assert_not_called()

    def _test_validate_env_ends_with_profile(self, mock_id):
        test_env = dict(role_original_data)
        test_env['parameters']['baremetal_prefix'] = 'baremetal-control'
        test_env = yaml.safe_dump(test_env)
        args = mock.Mock()
        args.id = mock_id
        with mock.patch('deploy.open',
                        mock.mock_open(read_data=test_env),
                        create=True) as mock_open:
            if not mock_id:
                self.assertRaises(RuntimeError, deploy._validate_env,
                                  args, 'foo.yaml')
            else:
                deploy._validate_env(args, 'foo.yaml')

    def test_validate_env_fails(self):
        self._test_validate_env_ends_with_profile(None)

    def test_validate_env_with_id(self):
        self._test_validate_env_ends_with_profile('foo')

    def test_validate_env(self):
        test_env = yaml.safe_dump(role_original_data)
        args = mock.Mock()
        args.id = None
        with mock.patch('deploy.open',
                        mock.mock_open(read_data=test_env),
                        create=True) as mock_open:
            deploy._validate_env(args, 'foo.yaml')


if __name__ == '__main__':
    unittest.main()

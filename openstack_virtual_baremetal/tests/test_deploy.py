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

import copy
import unittest
import yaml

import mock
import testtools

from openstack_virtual_baremetal import deploy


class TestProcessArgs(unittest.TestCase):
    def _basic_mock_args(self):
        """Return a mock with basic args set"""
        mock_args = mock.Mock()
        mock_args.name = None
        mock_args.quintupleo = False
        mock_args.id = None
        mock_args.env = []
        mock_args.role = []
        return mock_args

    def test_basic(self):
        mock_args = self._basic_mock_args()
        name, template = deploy._process_args(mock_args)
        self.assertEqual('baremetal', name)
        self.assertEqual('templates/virtual-baremetal.yaml', template)

    def test_name(self):
        mock_args = self._basic_mock_args()
        mock_args.name = 'foo'
        name, template = deploy._process_args(mock_args)
        self.assertEqual('foo', name)
        self.assertEqual('templates/virtual-baremetal.yaml', template)

    def test_quintupleo(self):
        mock_args = self._basic_mock_args()
        mock_args.quintupleo = True
        name, template = deploy._process_args(mock_args)
        self.assertEqual('quintupleo', name)
        self.assertEqual('templates/quintupleo.yaml', template)

    def test_quintupleo_name(self):
        mock_args = self._basic_mock_args()
        mock_args.name = 'foo'
        mock_args.quintupleo = True
        name, template = deploy._process_args(mock_args)
        self.assertEqual('foo', name)
        self.assertEqual('templates/quintupleo.yaml', template)

    def test_id_quintupleo(self):
        mock_args = self._basic_mock_args()
        mock_args.id = 'foo'
        self.assertRaises(RuntimeError, deploy._process_args, mock_args)

    def test_role_quintupleo(self):
        mock_args = self._basic_mock_args()
        mock_args.role = 'foo.yaml'
        self.assertRaises(RuntimeError, deploy._process_args, mock_args)

    def test_maintain_old_default(self):
        mock_args = self._basic_mock_args()
        mock_args.name = 'foo'
        mock_args.quintupleo = True
        name, template = deploy._process_args(mock_args)
        self.assertEqual('foo', name)
        self.assertEqual('templates/quintupleo.yaml', template)
        self.assertEqual(['env.yaml'], mock_args.env)

    def test_no_overwrite(self):
        mock_args = self._basic_mock_args()
        mock_args.quintupleo = True
        mock_args.id = 'foo'
        mock_args.env = ['env-foo.yaml']
        self.assertRaises(ValueError, deploy._process_args, mock_args)


test_env = u"""parameter_defaults:
  provision_net: provision
  public_net: public
  baremetal_prefix: baremetal
  bmc_prefix: bmc
"""
test_env_extra = u"""
  overcloud_internal_net: internalapi
  role: ''
"""
test_env_output = {
    'baremetal_prefix': 'baremetal-foo',
    'undercloud_name': 'undercloud-foo',
    'provision_net': 'provision-foo',
    'public_net': 'public-foo',
    'bmc_prefix': 'bmc-foo',
    'overcloud_internal_net': 'internal-foo',
    'overcloud_storage_net': 'storage-foo',
    'overcloud_storage_mgmt_net': 'storage_mgmt-foo',
    'overcloud_tenant_net': 'tenant-foo'
}


class TestIdEnv(unittest.TestCase):
    def test_add_identifier(self):
        env_data = {'parameter_defaults': {'foo': 'bar'}}
        deploy._add_identifier(env_data, 'foo', 'baz')
        self.assertEqual('bar-baz', env_data['parameter_defaults']['foo'])

    def test_add_identifier_different_section(self):
        env_data = {'parameter_defaults': {'foo': 'bar'}}
        deploy._add_identifier(env_data, 'foo', 'baz')
        self.assertEqual('bar-baz', env_data['parameter_defaults']['foo'])

    @mock.patch('openstack_virtual_baremetal.deploy._build_env_data')
    @mock.patch('yaml.safe_dump')
    def test_generate(self, mock_safe_dump, mock_bed):
        mock_args = mock.Mock()
        mock_args.id = 'foo'
        mock_args.env = ['foo.yaml']
        mock_bed.return_value = yaml.safe_load(test_env)
        path = deploy._generate_id_env(mock_args)
        self.assertEqual(['foo.yaml', 'env-foo.yaml'], path)
        dumped_dict = mock_safe_dump.call_args_list[0][0][0]
        for k, v in test_env_output.items():
            self.assertEqual(v, dumped_dict['parameter_defaults'][k])

    @mock.patch('openstack_virtual_baremetal.deploy._build_env_data')
    @mock.patch('yaml.safe_dump')
    def test_generate_undercloud_name(self, mock_safe_dump, mock_bed):
        mock_args = mock.Mock()
        mock_args.id = 'foo'
        mock_args.env = ['foo.yaml']
        env = (test_env + test_env_extra +
               '  undercloud_name: test-undercloud\n')
        mock_bed.return_value = yaml.safe_load(env)
        env_output = dict(test_env_output)
        env_output['undercloud_name'] = 'test-undercloud-foo'
        env_output['overcloud_internal_net'] = 'internalapi-foo'
        path = deploy._generate_id_env(mock_args)
        self.assertEqual(['foo.yaml', 'env-foo.yaml'], path)
        dumped_dict = mock_safe_dump.call_args_list[0][0][0]
        for k, v in env_output.items():
            self.assertEqual(v, dumped_dict['parameter_defaults'][k])

    @mock.patch('openstack_virtual_baremetal.deploy._build_env_data')
    @mock.patch('yaml.safe_dump')
    def test_generate_with_role(self, mock_safe_dump, mock_bed):
        mock_args = mock.Mock()
        mock_args.id = 'foo'
        mock_args.env = ['foo.yaml']
        env = (test_env + test_env_extra)
        mock_bed.return_value = yaml.safe_load(env)
        mock_bed.return_value['parameter_defaults']['role'] = 'compute'
        env_output = dict(test_env_output)
        env_output['overcloud_internal_net'] = 'internalapi-foo'
        env_output['baremetal_prefix'] = 'baremetal-foo-compute'
        path = deploy._generate_id_env(mock_args)
        self.assertEqual(['foo.yaml', 'env-foo.yaml'], path)
        dumped_dict = mock_safe_dump.call_args_list[0][0][0]
        for k, v in env_output.items():
            self.assertEqual(v, dumped_dict['parameter_defaults'][k])


# _process_role test data
role_base_data = {
    'parameter_defaults': {
        'overcloud_storage_mgmt_net': 'storage_mgmt-foo',
        'overcloud_internal_net': 'internal-foo',
        'overcloud_storage_net': 'storage-foo',
        'overcloud_tenant_net': 'tenant-foo',
        'provision_net': 'provision-foo',
        'public_net': 'public-foo',
        'private_net': 'private',
        'role': 'control',
        'os_user': 'admin',
        'key_name': 'default',
        'undercloud_name': 'undercloud-foo',
        'bmc_image': 'bmc-base',
        'baremetal_flavor': 'baremetal',
        'os_auth_url': 'http://1.1.1.1:5000/v2.0',
        'os_password': 'password',
        'os_tenant': 'admin',
        'bmc_prefix': 'bmc-foo',
        'undercloud_image': 'centos7-base',
        'baremetal_image': 'ipxe-boot',
        'external_net': 'external',
        'baremetal_prefix': 'baremetal-foo-control',
        'undercloud_flavor': 'undercloud-16',
        'node_count': 3,
        'bmc_flavor': 'bmc'
    },
    'resource_registry': {
        'OS::OVB::BaremetalNetworks': 'templates/baremetal-networks-all.yaml',
        'OS::OVB::BaremetalPorts':
            'templates/baremetal-ports-public-bond.yaml',
        'OS::OVB::BMCPort': 'templates/bmc-port.yaml'
    }
}
role_specific_data = {
    'parameter_defaults': {
        'role': 'compute',
        'key_name': 'default',
        'baremetal_flavor': 'baremetal',
        'baremetal_image': 'centos',
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
        'baremetal_prefix': 'baremetal',
        'public_net': 'public',
        'private_net': 'private',
        'provision_net': 'provision',
        'os_user': 'admin',
        'key_name': 'default',
        'undercloud_name': 'undercloud',
        'baremetal_flavor': 'baremetal',
        'os_auth_url': 'http://1.1.1.1:5000/v2.0',
        'bmc_image': 'bmc-base',
        'os_tenant': 'admin',
        'bmc_prefix': 'bmc',
        'undercloud_image': 'centos7-base',
        'baremetal_image': 'ipxe-boot',
        'external_net': 'external',
        'os_password': 'password',
        'undercloud_flavor': 'undercloud-16',
        'node_count': 3,
        'bmc_flavor': 'bmc'
    },
    'resource_registry': {
        'OS::OVB::BaremetalNetworks': 'templates/baremetal-networks-all.yaml',
        'OS::OVB::BaremetalPorts':
            'templates/baremetal-ports-public-bond.yaml',
        'OS::OVB::BMCPort': 'templates/bmc-port.yaml'
    }
}
# end _process_role test data


class TestDeploy(testtools.TestCase):
    def _test_deploy(self, mock_ghc, mock_tu, mock_poll, mock_cj, poll=False):
        mock_client = mock.Mock()
        mock_ghc.return_value = mock_client
        template_files = {'template.yaml': {'foo': 'bar'}}
        template = {'foo': 'bar'}
        mock_tu.get_template_contents.return_value = (
            template_files, template
        )
        env_files = {'templates/resource_registry.yaml': {'bar': 'baz'},
                     'env.yaml': {'parameter_defaults': {}}}
        env = {'parameter_defaults': {}}
        mock_tu.process_multiple_environments_and_files.return_value = (
            env_files, env
        )
        all_files = {}
        all_files.update(template_files)
        all_files.update(env_files)
        auth = {'os_user': 'admin',
                'os_password': 'password',
                'os_tenant': 'admin',
                'os_auth_url': 'http://1.1.1.1:5000/v2.0',
                }
        params = {'auth': auth}
        expected_params = {'cloud_data': params}
        mock_cj.return_value = params
        deploy._deploy('test', 'template.yaml', ['env.yaml', 'test.yaml'],
                       poll)
        mock_tu.get_template_contents.assert_called_once_with('template.yaml')
        process = mock_tu.process_multiple_environments_and_files
        process.assert_called_once_with(['templates/resource-registry.yaml',
                                         'env.yaml', 'test.yaml'])
        mock_client.stacks.create.assert_called_once_with(
            stack_name='test',
            template=template,
            environment=env,
            files=all_files,
            parameters=expected_params)
        if not poll:
            mock_poll.assert_not_called()
        else:
            mock_poll.assert_called_once_with('test', mock_client)

    @mock.patch('openstack_virtual_baremetal.auth._cloud_json')
    @mock.patch('openstack_virtual_baremetal.deploy._poll_stack')
    @mock.patch('openstack_virtual_baremetal.deploy.template_utils')
    @mock.patch('openstack_virtual_baremetal.deploy._get_heat_client')
    def test_deploy(self, mock_ghc, mock_tu, mock_poll, mock_cj):
        self._test_deploy(mock_ghc, mock_tu, mock_poll, mock_cj)

    @mock.patch('openstack_virtual_baremetal.auth._cloud_json')
    @mock.patch('openstack_virtual_baremetal.deploy._poll_stack')
    @mock.patch('openstack_virtual_baremetal.deploy.template_utils')
    @mock.patch('openstack_virtual_baremetal.deploy._get_heat_client')
    def test_deploy_poll(self, mock_ghc, mock_tu, mock_poll, mock_cj):
        self._test_deploy(mock_ghc, mock_tu, mock_poll, mock_cj, True)

    @mock.patch('time.sleep')
    def test_poll(self, mock_sleep):
        hclient = mock.Mock()
        stacks = [mock.Mock(), mock.Mock()]
        stacks[0].status = 'IN_PROGRESS'
        stacks[1].status = 'COMPLETE'
        hclient.stacks.get.side_effect = stacks
        deploy._poll_stack('foo', hclient)
        self.assertEqual(
            [
                mock.call('foo', resolve_outputs=False),
                mock.call('foo', resolve_outputs=False)
            ], hclient.stacks.get.mock_calls)

    @mock.patch('time.sleep')
    def test_poll_fail(self, mock_sleep):
        hclient = mock.Mock()
        stacks = [mock.Mock(), mock.Mock()]
        stacks[0].status = 'IN_PROGRESS'
        stacks[1].status = 'FAILED'
        hclient.stacks.get.side_effect = stacks
        self.assertRaises(RuntimeError, deploy._poll_stack, 'foo', hclient)
        self.assertEqual(
            [
                mock.call('foo', resolve_outputs=False),
                mock.call('foo', resolve_outputs=False)
            ], hclient.stacks.get.mock_calls)

    @mock.patch('time.sleep')
    def test_poll_retry(self, mock_sleep):
        hclient = mock.Mock()
        stacks = [mock.Mock(), Exception, mock.Mock()]
        stacks[0].status = 'IN_PROGRESS'
        stacks[2].status = 'COMPLETE'
        hclient.stacks.get.side_effect = stacks
        deploy._poll_stack('foo', hclient)
        self.assertEqual(
            [
                mock.call('foo', resolve_outputs=False),
                mock.call('foo', resolve_outputs=False),
                mock.call('foo', resolve_outputs=False)
            ], hclient.stacks.get.mock_calls)

    @mock.patch('openstack_virtual_baremetal.deploy._write_role_file')
    @mock.patch('openstack_virtual_baremetal.deploy._load_role_data')
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
                         output['parameter_defaults']['baremetal_prefix'])
        self.assertEqual('bmc-foo-compute',
                         output['parameter_defaults']['bmc_prefix'])
        # These should be inherited
        self.assertEqual('tenant-' + args.id,
                         output['parameter_defaults']['overcloud_tenant_net'])
        self.assertEqual('internal-' + args.id,
                         output['parameter_defaults']['overcloud_internal_net']
                         )
        self.assertEqual('storage-' + args.id,
                         output['parameter_defaults']['overcloud_storage_net'])
        self.assertEqual('storage_mgmt-' + args.id,
                         output['parameter_defaults'][
                             'overcloud_storage_mgmt_net'])
        # This parameter should be overrideable
        self.assertEqual('centos',
                         output['parameter_defaults']['baremetal_image'])
        # This should not be present in a role env, even if set in the file
        self.assertNotIn('OS::OVB::BaremetalNetworks',
                         output['resource_registry'])
        # This should be the value set in the role env, not the base one
        self.assertEqual(
            'templates/baremetal-ports-all.yaml',
            output['resource_registry']['OS::OVB::BaremetalPorts'])
        # This should be inherited from the base env
        self.assertEqual('templates/bmc-port.yaml',
                         output['resource_registry']['OS::OVB::BMCPort'])

    @mock.patch('openstack_virtual_baremetal.deploy._load_role_data')
    def test_process_role_invalid_name(self, mock_load):
        bad_role_specific_data = copy.deepcopy(role_specific_data)
        bad_role_specific_data['parameter_defaults']['role'] = 'foo_bar'
        mock_load.return_value = (role_base_data, bad_role_specific_data,
                                  role_original_data)
        args = mock.Mock()
        args.id = 'foo'
        self.assertRaises(RuntimeError, deploy._process_role,
                          'foo-foo_bar.yaml', 'foo.yaml', 'foo', args)

    @mock.patch('openstack_virtual_baremetal.deploy._deploy')
    @mock.patch('openstack_virtual_baremetal.deploy._process_role')
    def test_deploy_roles(self, mock_process, mock_deploy):
        args = mock.Mock()
        args.role = ['foo-compute.yaml']
        mock_process.return_value = ('env-foo-compute.yaml', 'compute')
        deploy._deploy_roles('foo', args, 'foo.yaml')
        mock_process.assert_called_once_with('foo-compute.yaml', 'foo.yaml',
                                             'foo', args)
        mock_deploy.assert_called_once_with('foo-compute',
                                            'templates/virtual-baremetal.yaml',
                                            ['env-foo-compute.yaml'],
                                            poll=True)

    @mock.patch('openstack_virtual_baremetal.deploy._process_role')
    def test_deploy_roles_empty(self, mock_process):
        args = mock.Mock()
        args.role = []
        deploy._deploy_roles('foo', args, 'foo.yaml')
        mock_process.assert_not_called()

    def _test_validate_env_ends_with_profile(self, mock_id, mock_bed):
        test_env = dict(role_original_data)
        test_env['parameter_defaults']['baremetal_prefix'] = (
            'baremetal-control')
        mock_bed.return_value = test_env
        args = mock.Mock()
        args.id = mock_id
        if not mock_id:
            self.assertRaises(RuntimeError, deploy._validate_env,
                              args, ['foo.yaml'])
        else:
            deploy._validate_env(args, ['foo.yaml'])

    @mock.patch('openstack_virtual_baremetal.deploy._build_env_data')
    def test_validate_env_fails(self, mock_bed):
        self._test_validate_env_ends_with_profile(None, mock_bed)

    @mock.patch('openstack_virtual_baremetal.deploy._build_env_data')
    def test_validate_env_with_id(self, mock_bed):
        self._test_validate_env_ends_with_profile('foo', mock_bed)

    @mock.patch('openstack_virtual_baremetal.deploy._build_env_data')
    def test_validate_env(self, mock_bed):
        mock_bed.return_value = role_original_data
        args = mock.Mock()
        args.id = None
        deploy._validate_env(args, ['foo.yaml'])


class TestGetHeatClient(testtools.TestCase):
    @mock.patch('openstack_virtual_baremetal.auth.OS_CLOUD', 'foo')
    @mock.patch('os_client_config.make_client')
    def test_os_cloud(self, mock_make_client):
        deploy._get_heat_client()
        mock_make_client.assert_called_once_with('orchestration', cloud='foo')


if __name__ == '__main__':
    unittest.main()

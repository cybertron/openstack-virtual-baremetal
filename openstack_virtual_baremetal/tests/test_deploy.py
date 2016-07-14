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

import mock

import deploy

class TestProcessArgs(unittest.TestCase):
    def test_basic(self):
        mock_args = mock.Mock()
        mock_args.name = None
        mock_args.quintupleo = False
        mock_args.id = None
        name, template = deploy._process_args(mock_args)
        self.assertEqual('baremetal', name)
        self.assertEqual('templates/virtual-baremetal.yaml', template)

    def test_name(self):
        mock_args = mock.Mock()
        mock_args.name = 'foo'
        mock_args.quintupleo = False
        mock_args.id = None
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

class TestDeploy(unittest.TestCase):
    @mock.patch('deploy.template_utils')
    @mock.patch('deploy._get_heat_client')
    def test_deploy(self, mock_ghc, mock_tu):
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
        deploy._deploy('test', 'template.yaml', 'env.yaml')
        mock_tu.get_template_contents.assert_called_once_with('template.yaml')
        process = mock_tu.process_multiple_environments_and_files
        process.assert_called_once_with(['templates/resource-registry.yaml',
                                         'env.yaml'])
        mock_client.stacks.create.assert_called_once_with(stack_name='test',
                                                          template=template,
                                                          environment=env,
                                                          files=all_files)

if __name__ == '__main__':
    unittest.main()

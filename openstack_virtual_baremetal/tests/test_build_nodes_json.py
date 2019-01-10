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
import json
import sys

import fixtures
import mock
import testtools

from openstack_virtual_baremetal import build_nodes_json


TEST_NODES = [{'arch': 'x86_64',
               'capabilities': 'boot_option:local',
               'cpu': 128,
               'disk': 1024,
               'mac': ['aa:aa:aa:aa:aa:aa'],
               'memory': 145055,
               'name': 'bm-0',
               'pm_addr': '1.1.1.1',
               'pm_password': 'password',
               'pm_type': 'pxe_ipmitool',
               'pm_user': 'admin'},
              {'arch': 'x86_64',
               'capabilities': 'boot_option:local',
               'cpu': 128,
               'disk': 1024,
               'mac': ['aa:aa:aa:aa:aa:ab'],
               'memory': 145055,
               'name': 'bm-1',
               'pm_addr': '1.1.1.2',
               'pm_password': 'password',
               'pm_type': 'pxe_ipmitool',
               'pm_user': 'admin'}]


class TestBuildNodesJson(testtools.TestCase):
    def test_parse_args(self):
        mock_argv = ['build-nodes-json', '--env', 'foo.yaml', '--bmc_prefix',
                     'bmc-foo', '--baremetal_prefix', 'baremetal-foo',
                     '--provision_net', 'provision-foo', '--nodes_json',
                     'nodes-foo.json', '--driver', 'ipmi',
                     '--physical_network',
                     ]
        with mock.patch.object(sys, 'argv', mock_argv):
            args = build_nodes_json._parse_args()
            self.assertEqual('foo.yaml', args.env)
            self.assertEqual('bmc-foo', args.bmc_prefix)
            self.assertEqual('baremetal-foo', args.baremetal_prefix)
            self.assertEqual('provision-foo', args.provision_net)
            self.assertEqual('nodes-foo.json', args.nodes_json)
            self.assertEqual('ipmi', args.driver)
            self.assertTrue(args.physical_network)

    def test_get_names_no_env(self):
        args = mock.Mock()
        args.env = None
        args.bmc_prefix = 'bmc-foo'
        args.baremetal_prefix = 'baremetal-foo'
        args.add_undercloud = False
        bmc_base, baremetal_base, undercloud_name = (
            build_nodes_json._get_names(args))
        self.assertEqual('bmc-foo', bmc_base)
        self.assertEqual('baremetal-foo', baremetal_base)
        self.assertEqual('undercloud', undercloud_name)

    def test_get_names_no_env_w_undercloud(self):
        args = mock.Mock()
        args.env = None
        args.bmc_prefix = 'bmc-foo'
        args.baremetal_prefix = 'baremetal-foo'
        args.add_undercloud = True
        bmc_base, baremetal_base, undercloud_name = (
            build_nodes_json._get_names(args))
        self.assertEqual('bmc-foo', bmc_base)
        self.assertEqual('baremetal-foo', baremetal_base)
        self.assertEqual('undercloud', undercloud_name)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    @mock.patch('yaml.safe_load')
    def test_get_names_env(self, mock_load, mock_open):
        args = mock.Mock()
        args.env = 'foo.yaml'
        args.add_undercloud = False
        mock_env = {
            'parameter_defaults': {
                'bmc_prefix': 'bmc-foo',
                'baremetal_prefix': 'baremetal-foo',
            },
        }
        mock_load.return_value = mock_env
        bmc_base, baremetal_base, undercloud_name = (
            build_nodes_json._get_names(args))
        self.assertEqual('bmc-foo', bmc_base)
        self.assertEqual('baremetal-foo', baremetal_base)
        self.assertIsNone(undercloud_name)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    @mock.patch('yaml.safe_load')
    def test_get_names_env_no_role(self, mock_load, mock_open):
        args = mock.Mock()
        args.env = 'foo.yaml'
        args.add_undercloud = False
        mock_env = {
            'parameter_defaults': {
                'bmc_prefix': 'bmc',
                'baremetal_prefix': 'baremetal',
                'role': 'foo',
            },
        }
        mock_load.return_value = mock_env
        bmc_base, baremetal_base, undercloud_name = (
            build_nodes_json._get_names(args))
        self.assertEqual('bmc', bmc_base)
        self.assertEqual('baremetal', baremetal_base)
        self.assertIsNone(undercloud_name)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    @mock.patch('yaml.safe_load')
    def test_get_names_env_strip_role(self, mock_load, mock_open):
        args = mock.Mock()
        args.env = 'foo.yaml'
        args.add_undercloud = False
        mock_env = {
            'parameter_defaults': {
                'bmc_prefix': 'bmc-foo',
                'baremetal_prefix': 'baremetal-foo-bar',
                'role': 'bar',
            },
        }
        mock_load.return_value = mock_env
        bmc_base, baremetal_base, undercloud_name = (
            build_nodes_json._get_names(args))
        self.assertEqual('bmc-foo', bmc_base)
        self.assertEqual('baremetal-foo', baremetal_base)
        self.assertIsNone(undercloud_name)

    @mock.patch('os_client_config.make_client')
    def test_get_clients_os_cloud(self, mock_make_client):
        self.useFixture(fixtures.EnvironmentVariable('OS_CLOUD', 'foo'))
        build_nodes_json._get_clients()
        calls = [mock.call('compute', cloud='foo'),
                 mock.call('network', cloud='foo'),
                 mock.call('image', cloud='foo')]
        self.assertEqual(calls, mock_make_client.mock_calls)

    @mock.patch('os_client_config.make_client')
    def test_get_clients_os_cloud_unset(self, mock_make_client):
        self.useFixture(fixtures.EnvironmentVariable('OS_CLOUD', None))
        build_nodes_json._get_clients()
        calls = [mock.call('compute', cloud=None),
                 mock.call('network', cloud=None),
                 mock.call('image', cloud=None)]
        self.assertEqual(calls, mock_make_client.mock_calls)

    def test_get_ports(self):
        neutron = mock.Mock()
        fake_fixed_ips = [{'subnet_id': 'provision_id'}]
        fake_ports = {
            'ports': [
                {'name': 'random',
                 'id': 'random_id',
                 'fixed_ips': fake_fixed_ips},
                {'name': 'bmc_1',
                 'id': 'bmc_1_id',
                 'fixed_ips': fake_fixed_ips},
                {'name': 'bmc_0',
                 'id': 'bmc_0_id',
                 'fixed_ips': fake_fixed_ips},
                {'name': 'baremetal_1',
                 'id': 'baremetal_1_id',
                 'fixed_ips': fake_fixed_ips},
                {'name': 'baremetal_0',
                 'id': 'baremetal_0_id',
                 'fixed_ips': fake_fixed_ips},
            ]
        }
        fake_subnets = {
            'subnets': [
                {'name': 'provision',
                 'id': 'provision_id'}
            ]
        }
        neutron.list_ports.return_value = fake_ports
        neutron.list_subnets.return_value = fake_subnets
        bmc_ports, bm_ports, provision_net_map = build_nodes_json._get_ports(
            neutron, 'bmc', 'baremetal')
        self.assertEqual([fake_ports['ports'][2], fake_ports['ports'][1]],
                         bmc_ports)
        self.assertEqual([fake_ports['ports'][4], fake_ports['ports'][3]],
                         bm_ports)
        self.assertEqual({'baremetal_0_id': 'provision',
                          'baremetal_1_id': 'provision'}, provision_net_map)

    def test_get_ports_mismatch(self):
        neutron = mock.Mock()
        fake_ports = {'ports': [{'name': 'bmc_0'}]}
        neutron.list_ports.return_value = fake_ports
        self.assertRaises(RuntimeError, build_nodes_json._get_ports, neutron,
                          'bmc', 'baremetal')

    def test_get_ports_multiple(self):
        neutron = mock.Mock()
        fake_fixed_ips = [{'subnet_id': 'provision_id'}]
        fake_ports = {
            'ports': [
                {'name': 'random',
                 'id': 'random_id',
                 'fixed_ips': fake_fixed_ips},
                {'name': 'bmc-foo_0',
                 'id': 'bmc_foo_0_id',
                 'fixed_ips': fake_fixed_ips},
                {'name': 'bmc-bar_0',
                 'id': 'bmc_bar_0_id',
                 'fixed_ips': fake_fixed_ips},
                {'name': 'baremetal-foo_0',
                 'id': 'baremetal_foo_0_id',
                 'fixed_ips': fake_fixed_ips},
                {'name': 'baremetal-bar_0',
                 'id': 'baremetal_bar_0_id',
                 'fixed_ips': fake_fixed_ips},
            ]
        }
        fake_subnets = {
            'subnets': [
                {'name': 'provision',
                 'id': 'provision_id'}
            ]
        }
        neutron.list_ports.return_value = fake_ports
        neutron.list_subnets.return_value = fake_subnets
        bmc_ports, bm_ports, provision_net_map = build_nodes_json._get_ports(
            neutron, 'bmc-foo', 'baremetal-foo')
        self.assertEqual([fake_ports['ports'][1]], bmc_ports)
        self.assertEqual([fake_ports['ports'][3]], bm_ports)

    def _fake_port(self, device_id, ip, mac):
        return {'device_id': device_id,
                'fixed_ips': [{'ip_address': ip}],
                }

    def _create_build_nodes_mocks(self, nova, servers):
        nova.servers.get.side_effect = servers
        servers[0].name = 'bm_0'
        servers[0].flavor = {'id': '1'}
        servers[0].addresses = {'provision': [{'OS-EXT-IPS-MAC:mac_addr':
                                               'aa:aa:aa:aa:aa:aa',
                                               'addr': '2.1.1.1'}]}
        servers[0].image = {'id': 'f00'}
        servers[0].id = '123abc'
        servers[1].name = 'bm_1'
        servers[1].flavor = {'id': '1'}
        servers[1].addresses = {'provision': [{'OS-EXT-IPS-MAC:mac_addr':
                                               'aa:aa:aa:aa:aa:ab',
                                               'addr': '2.1.1.2'}]}
        servers[1].image = {'id': 'f00'}
        servers[1].id = '456def'
        mock_flavor = mock.Mock()
        mock_flavor.vcpus = 128
        mock_flavor.ram = 145055
        mock_flavor.disk = 1024
        nova.flavors.get.return_value = mock_flavor

    @mock.patch('os_client_config.make_client')
    def test_build_nodes(self, mock_make_client):
        bmc_ports = [{'fixed_ips': [{'ip_address': '1.1.1.1'}]},
                     {'fixed_ips': [{'ip_address': '1.1.1.2'}]}
                     ]
        bm_ports = [{'device_id': '1', 'id': 'port_id_server1'},
                    {'device_id': '2', 'id': 'port_id_server2'}]
        provision_net_map = {'port_id_server1': 'provision',
                             'port_id_server2': 'provision',
                             'port_id_server3': 'provision', }
        physical_network = False
        nova = mock.Mock()
        servers = [mock.Mock(), mock.Mock(), mock.Mock()]
        self._create_build_nodes_mocks(nova, servers)
        servers[1].image = None
        mock_to_dict = {'os-extended-volumes:volumes_attached':
                        [{'id': 'v0lume'}]}
        servers[1].to_dict.return_value = mock_to_dict
        mock_cinder = mock.Mock()
        mock_make_client.return_value = mock_cinder
        mock_vol = mock.Mock()
        mock_vol.size = 100
        mock_cinder.volumes.get.return_value = mock_vol
        servers[2].name = 'undercloud'
        servers[2].flavor = {'id': '1'}
        servers[2].addresses = {'provision': [{'OS-EXT-IPS-MAC:mac_addr':
                                              'aa:aa:aa:aa:aa:ac'}]}
        servers[2].image = {'id': 'f00'}
        nova.servers.list.return_value = [servers[2]]
        ips_return_val = 'ips call value'
        nova.servers.ips.return_value = ips_return_val

        glance = mock.Mock()

        (nodes,
         extra_nodes,
         network_details) = build_nodes_json._build_nodes(
            nova, glance, bmc_ports, bm_ports, provision_net_map, 'bm',
            'undercloud', 'pxe_ipmitool', physical_network)
        expected_nodes = copy.deepcopy(TEST_NODES)
        expected_nodes[1]['disk'] = 100
        self.assertEqual(expected_nodes, nodes)
        self.assertEqual(1, len(extra_nodes))
        self.assertEqual('undercloud', extra_nodes[0]['name'])
        self.assertEqual(
            '2.1.1.1', network_details['bm_0']['ips']['provision'][0]['addr'])
        self.assertEqual(
            '2.1.1.2', network_details['bm_1']['ips']['provision'][0]['addr'])

    @mock.patch('os_client_config.make_client')
    def test_build_nodes_with_driver(self, mock_make_client):
        bmc_ports = [{'fixed_ips': [{'ip_address': '1.1.1.1'}]},
                     {'fixed_ips': [{'ip_address': '1.1.1.2'}]}
                     ]
        bm_ports = [{'device_id': '1', 'id': 'port_id_server1'},
                    {'device_id': '2', 'id': 'port_id_server2'}]
        provision_net_map = {'port_id_server1': 'provision',
                             'port_id_server2': 'provision',
                             'port_id_server3': 'provision', }
        physical_network = False
        nova = mock.Mock()
        servers = [mock.Mock(), mock.Mock(), mock.Mock()]
        self._create_build_nodes_mocks(nova, servers)
        servers[1].image = None
        mock_to_dict = {'os-extended-volumes:volumes_attached':
                        [{'id': 'v0lume'}]}
        servers[1].to_dict.return_value = mock_to_dict
        mock_cinder = mock.Mock()
        mock_make_client.return_value = mock_cinder
        mock_vol = mock.Mock()
        mock_vol.size = 100
        mock_cinder.volumes.get.return_value = mock_vol
        servers[2].name = 'undercloud'
        servers[2].flavor = {'id': '1'}
        servers[2].addresses = {'provision': [{'OS-EXT-IPS-MAC:mac_addr':
                                              'aa:aa:aa:aa:aa:ac'}]}
        servers[2].image = {'id': 'f00'}
        nova.servers.list.return_value = [servers[2]]
        ips_return_val = 'ips call value'
        nova.servers.ips.return_value = ips_return_val

        glance = mock.Mock()

        (nodes,
         extra_nodes,
         network_details) = build_nodes_json._build_nodes(
            nova, glance, bmc_ports, bm_ports, provision_net_map, 'bm',
            'undercloud', 'ipmi', physical_network)
        expected_nodes = copy.deepcopy(TEST_NODES)
        expected_nodes[1]['disk'] = 100
        for node in expected_nodes:
            node['pm_type'] = 'ipmi'
        self.assertEqual(expected_nodes, nodes)
        self.assertEqual(1, len(extra_nodes))
        self.assertEqual('undercloud', extra_nodes[0]['name'])
        self.assertEqual(
            '2.1.1.1', network_details['bm_0']['ips']['provision'][0]['addr'])
        self.assertEqual(
            '2.1.1.2', network_details['bm_1']['ips']['provision'][0]['addr'])

    def test_build_nodes_role_uefi(self):
        bmc_ports = [{'fixed_ips': [{'ip_address': '1.1.1.1'}]},
                     {'fixed_ips': [{'ip_address': '1.1.1.2'}]}
                     ]
        bm_ports = [{'device_id': '1', 'id': 'port_id_server1'},
                    {'device_id': '2', 'id': 'port_id_server2'}]
        provision_net_map = {'port_id_server1': 'provision',
                             'port_id_server2': 'provision',
                             'port_id_server3': 'provision', }
        physical_network = False
        nova = mock.Mock()
        servers = [mock.Mock(), mock.Mock(), mock.Mock()]
        self._create_build_nodes_mocks(nova, servers)
        servers[0].name = 'bm-foo-control_0'
        servers[1].name = 'bm-foo-control_1'
        ips_return_val = 'ips call value'
        nova.servers.ips.return_value = ips_return_val

        glance = mock.Mock()
        mock_image_get = mock.Mock()
        mock_image_get.get.return_value = 'uefi'
        glance.images.get.return_value = mock_image_get

        nodes, extra_nodes, _ = build_nodes_json._build_nodes(
            nova, glance, bmc_ports, bm_ports, provision_net_map, 'bm-foo',
            None, 'pxe_ipmitool', physical_network)
        expected_nodes = copy.deepcopy(TEST_NODES)
        expected_nodes[0]['name'] = 'bm-foo-control-0'
        expected_nodes[0]['capabilities'] = ('boot_option:local,'
                                             'boot_mode:uefi,'
                                             'profile:control')
        expected_nodes[1]['name'] = 'bm-foo-control-1'
        expected_nodes[1]['capabilities'] = ('boot_option:local,'
                                             'boot_mode:uefi,'
                                             'profile:control')
        self.assertEqual(expected_nodes, nodes)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    def test_write_nodes(self, mock_open):
        args = mock.Mock()
        mock_open.return_value = mock.MagicMock()
        args.nodes_json = 'test.json'
        args.network_details = False
        extra_nodes = []
        build_nodes_json._write_nodes(TEST_NODES, extra_nodes, {}, args)
        data = json.dumps({'nodes': TEST_NODES}, indent=2)
        f = mock_open.return_value.__enter__.return_value
        f.write.assert_called_once_with(data)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    def test_write_nodes_extra_node(self, mock_open):
        args = mock.Mock()
        mock_open.return_value = mock.MagicMock()
        args.nodes_json = 'test.json'
        args.network_details = True
        extra_nodes = [{'foo': 'bar'}]
        network_details = {'bar': 'baz'}
        build_nodes_json._write_nodes(TEST_NODES, extra_nodes,
                                      network_details, args)
        data = json.dumps({'nodes': TEST_NODES,
                           'extra_nodes': extra_nodes,
                           'network_details': network_details}, indent=2)
        f = mock_open.return_value.__enter__.return_value
        f.write.assert_called_once_with(data)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    def test_write_role_nodes(self, mock_open):
        test_nodes = copy.deepcopy(TEST_NODES)
        args = mock.Mock()
        args.nodes_json = 'test.json'
        build_nodes_json._write_role_nodes(test_nodes, args)
        mock_open.assert_not_called()

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    def test_write_role_nodes_profile(self, mock_open):
        test_nodes = copy.deepcopy(TEST_NODES)
        test_nodes[1]['capabilities'] = ('boot_option:local,'
                                         'boot_mode:uefi,'
                                         'profile:extra')
        args = mock.Mock()
        args.nodes_json = 'test.json'
        build_nodes_json._write_role_nodes(test_nodes, args)
        self.assertIn(mock.call('test-no-profile.json', 'w'),
                      mock_open.mock_calls)
        self.assertIn(mock.call('test-extra.json', 'w'),
                      mock_open.mock_calls)
        f = mock_open.return_value.__enter__.return_value
        f.write.assert_any_call(json.dumps({'nodes': [test_nodes[0]]},
                                           indent=2))
        f.write.assert_any_call(json.dumps({'nodes': [test_nodes[1]]},
                                           indent=2))

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.'
                '_write_role_nodes')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._write_nodes')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._build_nodes')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._get_ports')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._get_clients')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._get_names')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._parse_args')
    def test_main(self, mock_parse_args, mock_get_names, mock_get_clients,
                  mock_get_ports, mock_build_nodes, mock_write_nodes,
                  mock_write_role_nodes):
        args = mock.Mock()
        mock_parse_args.return_value = args
        bmc_base = mock.Mock()
        baremetal_base = mock.Mock()
        provision_net_map = mock.Mock()
        undercloud_name = 'undercloud'
        mock_get_names.return_value = (bmc_base, baremetal_base,
                                       undercloud_name)
        nova = mock.Mock()
        neutron = mock.Mock()
        glance = mock.Mock()
        mock_get_clients.return_value = (nova, neutron, glance)
        bmc_ports = mock.Mock()
        bm_ports = mock.Mock()
        mock_get_ports.return_value = (bmc_ports, bm_ports, provision_net_map)
        nodes = mock.Mock()
        extra_nodes = mock.Mock()
        network_details = mock.Mock()
        mock_build_nodes.return_value = (nodes, extra_nodes,
                                         network_details)

        build_nodes_json.main()

        mock_parse_args.assert_called_once_with()
        mock_get_names.assert_called_once_with(args)
        mock_get_clients.assert_called_once_with()
        mock_get_ports.assert_called_once_with(neutron, bmc_base,
                                               baremetal_base)
        mock_build_nodes.assert_called_once_with(nova, glance, bmc_ports,
                                                 bm_ports, provision_net_map,
                                                 baremetal_base,
                                                 undercloud_name,
                                                 args.driver,
                                                 args.physical_network)
        mock_write_nodes.assert_called_once_with(nodes, extra_nodes,
                                                 network_details, args)
        mock_write_role_nodes.assert_called_once_with(nodes, args)

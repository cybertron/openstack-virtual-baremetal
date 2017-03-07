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
                     'nodes-foo.json'
                     ]
        with mock.patch.object(sys, 'argv', mock_argv):
            args = build_nodes_json._parse_args()
            self.assertEqual('foo.yaml', args.env)
            self.assertEqual('bmc-foo', args.bmc_prefix)
            self.assertEqual('baremetal-foo', args.baremetal_prefix)
            self.assertEqual('provision-foo', args.provision_net)
            self.assertEqual('nodes-foo.json', args.nodes_json)

    def test_get_names_no_env(self):
        args = mock.Mock()
        args.env = None
        args.bmc_prefix = 'bmc-foo'
        args.baremetal_prefix = 'baremetal-foo'
        args.provision_net = 'provision-foo'
        args.add_undercloud = False
        bmc_base, baremetal_base, provision_net, undercloud_name = (
            build_nodes_json._get_names(args))
        self.assertEqual('bmc-foo', bmc_base)
        self.assertEqual('baremetal-foo', baremetal_base)
        self.assertEqual('provision-foo', provision_net)
        self.assertIsNone(undercloud_name)

    def test_get_names_no_env_w_undercloud(self):
        args = mock.Mock()
        args.env = None
        args.bmc_prefix = 'bmc-foo'
        args.baremetal_prefix = 'baremetal-foo'
        args.provision_net = 'provision-foo'
        args.add_undercloud = True
        bmc_base, baremetal_base, provision_net, undercloud_name = (
            build_nodes_json._get_names(args))
        self.assertEqual('bmc-foo', bmc_base)
        self.assertEqual('baremetal-foo', baremetal_base)
        self.assertEqual('provision-foo', provision_net)
        self.assertEqual('undercloud', undercloud_name)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    @mock.patch('yaml.safe_load')
    def test_get_names_env(self, mock_load, mock_open):
        args = mock.Mock()
        args.env = 'foo.yaml'
        args.add_undercloud = False
        mock_env = {'parameters':
                        {'bmc_prefix': 'bmc-foo',
                         'baremetal_prefix': 'baremetal-foo',
                         'provision_net': 'provision-foo'
                         },
                    'parameter_defaults': {}
                    }
        mock_load.return_value = mock_env
        bmc_base, baremetal_base, provision_net, undercloud_name = (
            build_nodes_json._get_names(args))
        self.assertEqual('bmc-foo', bmc_base)
        self.assertEqual('baremetal-foo', baremetal_base)
        self.assertEqual('provision-foo', provision_net)
        self.assertIsNone(undercloud_name)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    @mock.patch('yaml.safe_load')
    def test_get_names_env_no_role(self, mock_load, mock_open):
        args = mock.Mock()
        args.env = 'foo.yaml'
        args.add_undercloud = False
        mock_env = {'parameters':
                        {'bmc_prefix': 'bmc',
                         'baremetal_prefix': 'baremetal',
                         'provision_net': 'provision'
                         },
                    'parameter_defaults': {'role': 'foo'}
                    }
        mock_load.return_value = mock_env
        bmc_base, baremetal_base, provision_net, undercloud_name = (
            build_nodes_json._get_names(args))
        self.assertEqual('bmc', bmc_base)
        self.assertEqual('baremetal', baremetal_base)
        self.assertEqual('provision', provision_net)
        self.assertIsNone(undercloud_name)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    @mock.patch('yaml.safe_load')
    def test_get_names_env_strip_role(self, mock_load, mock_open):
        args = mock.Mock()
        args.env = 'foo.yaml'
        args.add_undercloud = False
        mock_env = {'parameters':
                        {'bmc_prefix': 'bmc-foo',
                         'baremetal_prefix': 'baremetal-foo-bar',
                         'provision_net': 'provision-foo'
                         },
                    'parameter_defaults': {'role': 'bar'}
                    }
        mock_load.return_value = mock_env
        bmc_base, baremetal_base, provision_net, undercloud_name = (
            build_nodes_json._get_names(args))
        self.assertEqual('bmc-foo', bmc_base)
        self.assertEqual('baremetal-foo', baremetal_base)
        self.assertEqual('provision-foo', provision_net)
        self.assertIsNone(undercloud_name)

    @mock.patch('os_client_config.make_client')
    def test_get_clients_os_cloud(self, mock_make_client):
        self.useFixture(fixtures.EnvironmentVariable('OS_CLOUD', 'foo'))
        build_nodes_json._get_clients()
        calls = [mock.call('compute', cloud='foo'),
                 mock.call('network', cloud='foo')]
        self.assertEqual(calls, mock_make_client.mock_calls)

    def _test_get_clients_env(self, mock_nova, mock_neutron):
        self.useFixture(fixtures.EnvironmentVariable('OS_USERNAME', 'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PASSWORD', 'pw'))
        self.useFixture(fixtures.EnvironmentVariable('OS_TENANT_NAME',
                                                     'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_AUTH_URL', 'admin'))
        mock_nova_client = mock.Mock()
        mock_nova.return_value = mock_nova_client
        mock_neutron_client = mock.Mock()
        mock_neutron.return_value = mock_neutron_client
        nova, neutron = build_nodes_json._get_clients()
        self.assertEqual(mock_nova_client, nova)
        self.assertEqual(mock_neutron_client, neutron)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.nc.__version__',
                ('6', '0', '0'))
    @mock.patch('neutronclient.v2_0.client.Client')
    @mock.patch('novaclient.client.Client')
    def test_get_clients_env_6(self, mock_nova, mock_neutron):
        self._test_get_clients_env(mock_nova, mock_neutron)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.nc.__version__',
                ('7', '0', '0'))
    @mock.patch('neutronclient.v2_0.client.Client')
    @mock.patch('novaclient.client.Client')
    def test_get_clients_env_7(self, mock_nova, mock_neutron):
        self._test_get_clients_env(mock_nova, mock_neutron)

    @mock.patch('openstack_virtual_baremetal.auth._get_keystone_session')
    @mock.patch('neutronclient.v2_0.client.Client')
    @mock.patch('novaclient.client.Client')
    def test_get_clients_env_v3(self, mock_nova, mock_neutron, mock_gks):
        self.useFixture(fixtures.EnvironmentVariable('OS_USERNAME', 'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PASSWORD', 'pw'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PROJECT_NAME',
                                                     'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_AUTH_URL', 'auth/v3'))
        self.useFixture(fixtures.EnvironmentVariable('OS_USER_DOMAIN_ID',
                                                     'default'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PROJECT_DOMAIN_ID',
                                                     'default'))
        mock_nova_client = mock.Mock()
        mock_nova.return_value = mock_nova_client
        mock_neutron_client = mock.Mock()
        mock_neutron.return_value = mock_neutron_client
        mock_session_inst = mock.Mock()
        mock_gks.return_value = mock_session_inst
        nova, neutron = build_nodes_json._get_clients()
        mock_neutron.assert_called_once_with(session=mock_session_inst)
        self.assertEqual(mock_nova_client, nova)
        self.assertEqual(mock_neutron_client, neutron)

    @mock.patch('sys.exit')
    def test_get_clients_missing(self, mock_exit):
        build_nodes_json._get_clients()
        mock_exit.assert_called_once_with(1)

    @mock.patch('sys.exit')
    def test_get_clients_missing_v3(self, mock_exit):
        self.useFixture(fixtures.EnvironmentVariable('OS_AUTH_URL',
                                                     'http://host/v3'))
        build_nodes_json._get_clients()
        mock_exit.assert_called_once_with(1)

    def test_get_ports(self):
        neutron = mock.Mock()
        fake_ports = {'ports':
                          [{'name': 'random'},
                           {'name': 'bmc_1'},
                           {'name': 'bmc_0'},
                           {'name': 'baremetal_1'},
                           {'name': 'baremetal_0'},
                           ]
                          }
        neutron.list_ports.return_value = fake_ports
        bmc_ports, bm_ports = build_nodes_json._get_ports(neutron, 'bmc',
                                                          'baremetal')
        self.assertEqual([{'name': 'bmc_0'}, {'name': 'bmc_1'}], bmc_ports)
        self.assertEqual([{'name': 'baremetal_0'}, {'name': 'baremetal_1'}],
                         bm_ports)

    def test_get_ports_mismatch(self):
        neutron = mock.Mock()
        fake_ports = {'ports': [{'name': 'bmc_0'}]}
        neutron.list_ports.return_value = fake_ports
        self.assertRaises(RuntimeError, build_nodes_json._get_ports, neutron,
                          'bmc', 'baremetal')

    def test_get_ports_multiple(self):
        neutron = mock.Mock()
        fake_ports = {'ports':
                          [{'name': 'random'},
                           {'name': 'bmc-foo_0'},
                           {'name': 'bmc-bar_0'},
                           {'name': 'baremetal-foo_0'},
                           {'name': 'baremetal-bar_0'},
                           ]
                          }
        neutron.list_ports.return_value = fake_ports
        bmc_ports, bm_ports = build_nodes_json._get_ports(neutron, 'bmc-foo',
                                                          'baremetal-foo')
        self.assertEqual([{'name': 'bmc-foo_0'}], bmc_ports)
        self.assertEqual([{'name': 'baremetal-foo_0'}], bm_ports)

    def _fake_port(self, device_id, ip, mac):
        return {'device_id': device_id,
                'fixed_ips': [{'ip_address': ip}],
                }

    def _create_build_nodes_mocks(self, nova, servers):
        nova.servers.get.side_effect = servers
        servers[0].name = 'bm_0'
        servers[0].flavor = {'id': '1'}
        servers[0].addresses = {'provision': [{'OS-EXT-IPS-MAC:mac_addr':
                                                   'aa:aa:aa:aa:aa:aa'}]}
        servers[0].image = {'id': 'f00'}
        servers[1].name = 'bm_1'
        servers[1].flavor = {'id': '1'}
        servers[1].addresses = {'provision': [{'OS-EXT-IPS-MAC:mac_addr':
                                                   'aa:aa:aa:aa:aa:ab'}]}
        servers[1].image = {'id': 'f00'}
        mock_flavor = mock.Mock()
        mock_flavor.vcpus = 128
        mock_flavor.ram = 145055
        mock_flavor.disk = 1024
        nova.flavors.get.return_value = mock_flavor

    def test_build_nodes(self):
        bmc_ports = [{'fixed_ips': [{'ip_address': '1.1.1.1'}]},
                     {'fixed_ips': [{'ip_address': '1.1.1.2'}]}
                     ]
        bm_ports = [{'device_id': '1'}, {'device_id': '2'}]
        nova = mock.Mock()
        servers = [mock.Mock(), mock.Mock(), mock.Mock()]
        self._create_build_nodes_mocks(nova, servers)
        servers[2].name = 'undercloud'
        servers[2].flavor = {'id': '1'}
        servers[2].addresses = {'provision': [{'OS-EXT-IPS-MAC:mac_addr':
                                                   'aa:aa:aa:aa:aa:ac'}]}
        servers[2].image = {'id': 'f00'}
        nova.servers.list.return_value = [servers[2]]
        ips_return_val = 'ips call value'
        nova.servers.ips.return_value = ips_return_val

        nodes, bmc_bm_pairs, extra_nodes = build_nodes_json._build_nodes(
            nova, bmc_ports, bm_ports, 'provision', 'bm', 'undercloud')
        expected_nodes = TEST_NODES
        self.assertEqual(expected_nodes, nodes)
        self.assertEqual([('1.1.1.1', 'bm_0'), ('1.1.1.2', 'bm_1')],
                         bmc_bm_pairs)
        self.assertEqual(1, len(extra_nodes))
        self.assertEqual('undercloud', extra_nodes[0]['name'])

    def test_build_nodes_role_uefi(self):
        bmc_ports = [{'fixed_ips': [{'ip_address': '1.1.1.1'}]},
                     {'fixed_ips': [{'ip_address': '1.1.1.2'}]}
                     ]
        bm_ports = [{'device_id': '1'}, {'device_id': '2'}]
        nova = mock.Mock()
        servers = [mock.Mock(), mock.Mock(), mock.Mock()]
        self._create_build_nodes_mocks(nova, servers)
        servers[0].name = 'bm-foo-control_0'
        servers[1].name = 'bm-foo-control_1'
        ips_return_val = 'ips call value'
        nova.servers.ips.return_value = ips_return_val
        mock_image_get = mock.Mock()
        nova.images.get.return_value = mock_image_get
        mock_image_get.metadata.get.return_value = 'uefi'

        nodes, bmc_bm_pairs, extra_nodes = build_nodes_json._build_nodes(
            nova, bmc_ports, bm_ports, 'provision', 'bm-foo', None)
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
        self.assertEqual([('1.1.1.1', 'bm-foo-control_0'),
                          ('1.1.1.2', 'bm-foo-control_1')],
                         bmc_bm_pairs)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    def test_write_nodes(self, mock_open):
        args = mock.Mock()
        mock_open.return_value = mock.MagicMock()
        args.nodes_json = 'test.json'
        extra_nodes = []
        build_nodes_json._write_nodes(TEST_NODES, extra_nodes, args)
        data = json.dumps({'nodes': TEST_NODES}, indent=2)
        f = mock_open.return_value.__enter__.return_value
        f.write.assert_called_once_with(data)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    def test_write_nodes_extra_node(self, mock_open):
        args = mock.Mock()
        mock_open.return_value = mock.MagicMock()
        args.nodes_json = 'test.json'
        extra_nodes = [{'foo': 'bar'}]
        build_nodes_json._write_nodes(TEST_NODES, extra_nodes, args)
        data = json.dumps({'nodes': TEST_NODES,
                           'extra_nodes': extra_nodes}, indent=2)
        f = mock_open.return_value.__enter__.return_value
        f.write.assert_called_once_with(data)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json.open',
                create=True)
    def test_write_pairs(self, mock_open):
        pairs = [('1.1.1.1', 'bm_0'), ('1.1.1.2', 'bm_1')]
        mock_open.return_value = mock.MagicMock()
        build_nodes_json._write_pairs(pairs)
        calls = [mock.call('# A list of BMC addresses and the name of the '
                           'instance that BMC manages.\n'),
                 mock.call('1.1.1.1 bm_0\n'),
                 mock.call('1.1.1.2 bm_1\n'),
                 ]
        f = mock_open.return_value.__enter__.return_value
        self.assertEqual(calls, f.write.mock_calls)

    @mock.patch('openstack_virtual_baremetal.build_nodes_json._write_pairs')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._write_nodes')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._build_nodes')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._get_ports')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._get_clients')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._get_names')
    @mock.patch('openstack_virtual_baremetal.build_nodes_json._parse_args')
    def test_main(self, mock_parse_args, mock_get_names, mock_get_clients,
                  mock_get_ports, mock_build_nodes, mock_write_nodes,
                  mock_write_pairs):
        args = mock.Mock()
        mock_parse_args.return_value = args
        bmc_base = mock.Mock()
        baremetal_base = mock.Mock()
        provision_net = mock.Mock()
        undercloud_name = 'undercloud'
        mock_get_names.return_value = (bmc_base, baremetal_base, provision_net,
                                       undercloud_name)
        nova = mock.Mock()
        neutron = mock.Mock()
        mock_get_clients.return_value = (nova, neutron)
        bmc_ports = mock.Mock()
        bm_ports = mock.Mock()
        mock_get_ports.return_value = (bmc_ports, bm_ports)
        nodes = mock.Mock()
        pairs = mock.Mock()
        extra_nodes = mock.Mock()
        mock_build_nodes.return_value = (nodes, pairs, extra_nodes)

        build_nodes_json.main()

        mock_parse_args.assert_called_once_with()
        mock_get_names.assert_called_once_with(args)
        mock_get_clients.assert_called_once_with()
        mock_get_ports.assert_called_once_with(neutron, bmc_base,
                                               baremetal_base)
        mock_build_nodes.assert_called_once_with(nova, bmc_ports, bm_ports,
                                                 provision_net, baremetal_base,
                                                 undercloud_name)
        mock_write_nodes.assert_called_once_with(nodes, extra_nodes, args)
        mock_write_pairs.assert_called_once_with(pairs)


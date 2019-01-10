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

import sys
import unittest

import fixtures
import mock
from novaclient import exceptions
import testtools

from openstack_virtual_baremetal import openstackbmc


@mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
            'log')
@mock.patch('pyghmi.ipmi.bmc.Bmc.__init__')
@mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
            '_find_instance')
@mock.patch('os_client_config.make_client')
class TestOpenStackBmcInit(testtools.TestCase):
    def test_init_os_cloud(self, mock_make_client, mock_find_instance,
                           mock_bmc_init, mock_log):
        mock_client = mock.Mock()
        mock_server = mock.Mock()
        mock_server.name = 'foo-instance'
        mock_client.servers.get.return_value = mock_server
        mock_make_client.return_value = mock_client
        mock_find_instance.return_value = 'abc-123'
        bmc = openstackbmc.OpenStackBmc(authdata={'admin': 'password'},
                                        port=623,
                                        address='::ffff:127.0.0.1',
                                        instance='foo',
                                        cache_status=False,
                                        os_cloud='bar'
                                        )

        mock_make_client.assert_called_once_with('compute', cloud='bar')
        mock_find_instance.assert_called_once_with('foo')
        self.assertEqual('abc-123', bmc.instance)
        mock_client.servers.get.assert_called_once_with('abc-123')
        mock_log.assert_called_once_with('Managing instance: %s UUID: %s' %
                                         ('foo-instance', 'abc-123'))

    @mock.patch('time.sleep')
    def test_init_retry(self, _, mock_make_client, mock_find_instance,
                        mock_bmc_init, mock_log):
        self.useFixture(fixtures.EnvironmentVariable('OS_CLOUD', None))
        mock_client = mock.Mock()
        mock_server = mock.Mock()
        mock_server.name = 'foo-instance'
        mock_client.servers.get.return_value = mock_server
        mock_make_client.return_value = mock_client
        mock_find_instance.side_effect = (Exception, 'abc-123')
        bmc = openstackbmc.OpenStackBmc(authdata={'admin': 'password'},
                                        port=623,
                                        address='::ffff:127.0.0.1',
                                        instance='foo',
                                        cache_status=False,
                                        os_cloud='foo'
                                        )
        mock_make_client.assert_called_once_with('compute', cloud='foo')
        find_calls = [mock.call('foo'), mock.call('foo')]
        self.assertEqual(find_calls, mock_find_instance.mock_calls)
        self.assertEqual('abc-123', bmc.instance)
        mock_client.servers.get.assert_called_once_with('abc-123')
        log_calls = [mock.call('Exception finding instance "%s": %s' %
                               ('foo', '')),
                     mock.call('Managing instance: %s UUID: %s' %
                               ('foo-instance', 'abc-123'))
                     ]
        self.assertEqual(log_calls, mock_log.mock_calls)


@mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
            '__init__', return_value=None)
@mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
            'log')
@mock.patch('novaclient.client.Client')
class TestOpenStackBmc(unittest.TestCase):
    def _create_bmc(self, mock_nova):
        self.mock_client = mock.Mock()
        mock_nova.return_value = self.mock_client
        self.bmc = openstackbmc.OpenStackBmc(authdata={'admin': 'password'},
                                             port=623,
                                             address='::ffff:127.0.0.1',
                                             instance='foo',
                                             cache_status=False,
                                             os_cloud='bar'
                                             )
        self.bmc.novaclient = self.mock_client
        self.bmc.instance = 'abc-123'
        self.bmc.cached_status = None
        self.bmc.target_status = None
        self.bmc.cache_status = False

    def test_find_instance(self, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        mock_server = mock.Mock()
        self.mock_client.servers.get.return_value = mock_server
        instance = self.bmc._find_instance('abc-123')
        self.assertEqual('abc-123', instance)

    def test_find_instance_by_name(self, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        mock_server = mock.Mock()
        mock_server.id = 'abc-123'
        self.mock_client.servers.get.side_effect = exceptions.NotFound('foo')
        self.mock_client.servers.list.return_value = [mock_server]
        instance = self.bmc._find_instance('abc-123')
        self.assertEqual('abc-123', instance)

    @mock.patch('sys.exit')
    def test_find_instance_multiple(self, mock_exit, mock_nova, mock_log,
                                    mock_init):
        self._create_bmc(mock_nova)
        mock_server = mock.Mock()
        self.mock_client.servers.get.side_effect = exceptions.NotFound('foo')
        self.mock_client.servers.list.return_value = [mock_server, mock_server]
        self.bmc._find_instance('abc-123')
        mock_exit.assert_called_once_with(1)

    @mock.patch('sys.exit')
    def test_find_instance_not_found(self, mock_exit, mock_nova, mock_log,
                                     mock_init):
        self._create_bmc(mock_nova)
        self.mock_client.servers.get.side_effect = exceptions.NotFound('foo')
        self.mock_client.servers.list.return_value = []
        self.bmc._find_instance('abc-123')
        mock_exit.assert_called_once_with(1)

    def test_get_boot_device(self, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        mock_server = mock.Mock()
        mock_server.metadata.get.return_value = None
        self.mock_client.servers.get.return_value = mock_server
        device = self.bmc.get_boot_device()
        self.assertEqual('hd', device)

    def test_get_boot_device_network(self, mock_nova, mock_log, mock_init):
        def fake_get(key):
            if key == 'libvirt:pxe-first':
                return '1'
            return ''
        self._create_bmc(mock_nova)
        mock_server = mock.Mock()
        mock_server.metadata.get.side_effect = fake_get
        self.mock_client.servers.get.return_value = mock_server
        device = self.bmc.get_boot_device()
        self.assertEqual('network', device)

    def test_set_boot_device_hd(self, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        mock_server = mock.Mock()
        self.mock_client.servers.get.return_value = mock_server
        self.bmc.set_boot_device('hd')
        self.mock_client.servers.set_meta_item.assert_called_once_with(
            mock_server,
            'libvirt:pxe-first',
            '')

    def test_set_boot_device_net(self, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        mock_server = mock.Mock()
        self.mock_client.servers.get.return_value = mock_server
        self.bmc.set_boot_device('network')
        self.mock_client.servers.set_meta_item.assert_called_once_with(
            mock_server,
            'libvirt:pxe-first',
            '1')

    def test_instance_active(self, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        mock_server = mock.Mock()
        mock_server.status = 'ACTIVE'
        self.mock_client.servers.get.return_value = mock_server
        self.assertTrue(self.bmc._instance_active())

    def test_instance_inactive(self, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        mock_server = mock.Mock()
        mock_server.status = 'SHUTOFF'
        self.mock_client.servers.get.return_value = mock_server
        self.assertFalse(self.bmc._instance_active())

    def test_instance_active_mismatch(self, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        mock_server = mock.Mock()
        mock_server.status = 'ACTIVE'
        self.mock_client.servers.get.return_value = mock_server
        self.bmc.target_status = 'ACTIVE'
        self.bmc.cached_status = 'SHUTOFF'
        self.bmc.cache_status = True
        self.assertTrue(self.bmc._instance_active())

    def test_instance_active_cached(self, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        self.bmc.target_status = 'ACTIVE'
        self.bmc.cached_status = 'ACTIVE'
        self.bmc.cache_status = True
        self.assertTrue(self.bmc._instance_active())
        self.assertFalse(self.mock_client.servers.get.called)

    def test_cache_disabled(self, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        self.bmc.target_status = 'ACTIVE'
        self.bmc.cached_status = 'ACTIVE'
        mock_server = mock.Mock()
        mock_server.status = 'SHUTOFF'
        self.mock_client.servers.get.return_value = mock_server
        self.assertFalse(self.bmc._instance_active())

    @mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
                '_instance_active')
    def test_get_power_state(self, mock_active, mock_nova, mock_log,
                             mock_init):
        self._create_bmc(mock_nova)
        mock_active.return_value = True
        self.assertTrue(self.bmc.get_power_state())

    @mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
                '_instance_active')
    def test_power_off(self, mock_active, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        mock_active.return_value = True
        self.bmc.power_off()
        self.mock_client.servers.stop.assert_called_once_with('abc-123')
        self.assertEqual('SHUTOFF', self.bmc.target_status)

    @mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
                '_instance_active')
    def test_power_off_conflict(self, mock_active, mock_nova, mock_log,
                                mock_init):
        self._create_bmc(mock_nova)
        mock_active.return_value = True
        self.mock_client.servers.stop.side_effect = exceptions.Conflict('a')
        self.bmc.power_off()
        self.mock_client.servers.stop.assert_called_once_with('abc-123')
        mock_log.assert_called_once_with('Ignoring exception: '
                                         '"Conflict (HTTP a)"')

    @mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
                '_instance_active')
    def test_power_off_already_off(self, mock_active, mock_nova, mock_log,
                                   mock_init):
        self._create_bmc(mock_nova)
        mock_active.return_value = False
        val = self.bmc.power_off()
        self.assertIsNone(val)
        mock_log.assert_called_once_with('abc-123 is already off.')

    @mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
                '_instance_active')
    def test_power_on(self, mock_active, mock_nova, mock_log, mock_init):
        self._create_bmc(mock_nova)
        mock_active.return_value = False
        self.bmc.power_on()
        self.mock_client.servers.start.assert_called_once_with('abc-123')
        self.assertEqual('ACTIVE', self.bmc.target_status)

    @mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
                '_instance_active')
    def test_power_on_conflict(self, mock_active, mock_nova, mock_log,
                               mock_init):
        self._create_bmc(mock_nova)
        mock_active.return_value = False
        self.mock_client.servers.start.side_effect = exceptions.Conflict('a')
        self.bmc.power_on()
        self.mock_client.servers.start.assert_called_once_with('abc-123')
        mock_log.assert_called_once_with('Ignoring exception: '
                                         '"Conflict (HTTP a)"')

    @mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc.'
                '_instance_active')
    def test_power_on_already_on(self, mock_active, mock_nova, mock_log,
                                 mock_init):
        self._create_bmc(mock_nova)
        mock_active.return_value = True
        val = self.bmc.power_on()
        self.assertIsNone(val)
        mock_log.assert_called_once_with('abc-123 is already on.')


class TestMain(unittest.TestCase):
    @mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc')
    def test_main(self, mock_bmc):
        mock_instance = mock.Mock()
        mock_bmc.return_value = mock_instance
        mock_argv = ['openstackbmc', '--port', '111', '--address', '1.2.3.4',
                     '--instance', 'foobar', '--os-cloud', 'foo']
        with mock.patch.object(sys, 'argv', mock_argv):
            openstackbmc.main()
        mock_bmc.assert_called_once_with({'admin': 'password'},
                                         port=111,
                                         address='::ffff:1.2.3.4',
                                         instance='foobar',
                                         cache_status=False,
                                         os_cloud='foo'
                                         )
        mock_instance.listen.assert_called_once_with()

    @mock.patch('openstack_virtual_baremetal.openstackbmc.OpenStackBmc')
    def test_main_default_addr(self, mock_bmc):
        mock_instance = mock.Mock()
        mock_bmc.return_value = mock_instance
        mock_argv = ['openstackbmc', '--port', '111',
                     '--instance', 'foobar', '--os-cloud', 'bar']
        with mock.patch.object(sys, 'argv', mock_argv):
            openstackbmc.main()
        mock_bmc.assert_called_once_with({'admin': 'password'},
                                         port=111,
                                         address='::',
                                         instance='foobar',
                                         cache_status=False,
                                         os_cloud='bar'
                                         )
        mock_instance.listen.assert_called_once_with()

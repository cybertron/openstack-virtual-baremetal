# Copyright 2017 Red Hat Inc.
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

import fixtures
import mock
import testtools

from openstack_virtual_baremetal import auth


class TestValidateAuthParameters(testtools.TestCase):
    def test_validate_passes_v2(self):
        auth._validate_auth_parameters('admin', 'password', 'admin',
                                       'auth_url', '', '', '')

    def test_validate_passes_v3(self):
        auth._validate_auth_parameters('admin', 'password', '',
                                       'auth_url/v3', 'admin', 'default',
                                       'default')

    @mock.patch('sys.exit')
    def test_validate_fails_v2(self, mock_exit):
        auth._validate_auth_parameters('admin', 'password', '',
                                       'auth_url', '', '', '')
        mock_exit.assert_called_once_with(1)

    @mock.patch('sys.exit')
    def test_validate_fails_v3(self, mock_exit):
        auth._validate_auth_parameters('admin', 'password', '',
                                       'auth_url/v3', '', '', '')
        mock_exit.assert_called_once_with(1)


class TestCreateAuthParameters(testtools.TestCase):
    @mock.patch('openstack_virtual_baremetal.auth.OS_CLOUD', 'foo')
    @mock.patch('os_client_config.OpenStackConfig')
    def test_create_auth_parameters_os_cloud(self, mock_osc):
        mock_data = mock.Mock()
        mock_data.config = {'auth': {'username': 'admin',
                                     'password': 'password',
                                     'project_name': 'admin',
                                     'auth_url': 'http://host:5000',
                                     }}
        mock_instance = mock.Mock()
        mock_instance.get_one_cloud.return_value = mock_data
        mock_osc.return_value = mock_instance
        result = auth._create_auth_parameters()
        expected = {'os_user': 'admin',
                    'os_password': 'password',
                    'os_tenant': 'admin',
                    'os_auth_url': 'http://host:5000',
                    'os_project': 'admin',
                    'os_user_domain': '',
                    'os_project_domain': '',
                    }
        self.assertEqual(expected, result)

    @mock.patch('openstack_virtual_baremetal.auth.OS_CLOUD', 'foo')
    @mock.patch('os_client_config.OpenStackConfig')
    def test_create_auth_parameters_os_cloud_v3_id(self, mock_osc):
        mock_data = mock.Mock()
        mock_data.config = {'auth': {'username': 'admin',
                                     'password': 'password',
                                     'project_name': 'admin',
                                     'auth_url': 'http://host:5000',
                                     'user_domain_id': 'default',
                                     'project_domain_id': 'default',
                                     }}
        mock_instance = mock.Mock()
        mock_instance.get_one_cloud.return_value = mock_data
        mock_osc.return_value = mock_instance
        result = auth._create_auth_parameters()
        expected = {'os_user': 'admin',
                    'os_password': 'password',
                    'os_tenant': 'admin',
                    'os_auth_url': 'http://host:5000',
                    'os_project': 'admin',
                    'os_user_domain': 'default',
                    'os_project_domain': 'default',
                    }
        self.assertEqual(expected, result)

    @mock.patch('openstack_virtual_baremetal.auth.OS_CLOUD', 'foo')
    @mock.patch('os_client_config.OpenStackConfig')
    def test_create_auth_parameters_os_cloud_v3_name(self, mock_osc):
        mock_data = mock.Mock()
        mock_data.config = {'auth': {'username': 'admin',
                                     'password': 'password',
                                     'project_name': 'admin',
                                     'auth_url': 'http://host:5000',
                                     'user_domain_name': 'default',
                                     'project_domain_name': 'default',
                                     }}
        mock_instance = mock.Mock()
        mock_instance.get_one_cloud.return_value = mock_data
        mock_osc.return_value = mock_instance
        result = auth._create_auth_parameters()
        expected = {'os_user': 'admin',
                    'os_password': 'password',
                    'os_tenant': 'admin',
                    'os_auth_url': 'http://host:5000',
                    'os_project': 'admin',
                    'os_user_domain': 'default',
                    'os_project_domain': 'default',
                    }
        self.assertEqual(expected, result)

    def test_create_auth_parameters_env_v3(self):
        self.useFixture(fixtures.EnvironmentVariable('OS_USERNAME', 'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PASSWORD', 'pw'))
        self.useFixture(fixtures.EnvironmentVariable('OS_TENANT_NAME',
                                                     'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_AUTH_URL', 'auth/v3'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PROJECT_NAME',
                                                     'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_USER_DOMAIN_ID',
                                                     'default'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PROJECT_DOMAIN_ID',
                                                     'default'))
        result = auth._create_auth_parameters()
        expected = {'os_user': 'admin',
                    'os_password': 'pw',
                    'os_tenant': 'admin',
                    'os_auth_url': 'auth/v3',
                    'os_project': 'admin',
                    'os_user_domain': 'default',
                    'os_project_domain': 'default',
                    }
        self.assertEqual(expected, result)

    def test_create_auth_parameters_env_name(self):
        self.useFixture(fixtures.EnvironmentVariable('OS_USERNAME', 'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PASSWORD', 'pw'))
        self.useFixture(fixtures.EnvironmentVariable('OS_TENANT_NAME',
                                                     None))
        self.useFixture(fixtures.EnvironmentVariable('OS_AUTH_URL', 'auth/v3'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PROJECT_NAME',
                                                     'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_USER_DOMAIN_NAME',
                                                     'default'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PROJECT_DOMAIN_NAME',
                                                     'default'))
        result = auth._create_auth_parameters()
        expected = {'os_user': 'admin',
                    'os_password': 'pw',
                    'os_tenant': '',
                    'os_auth_url': 'auth/v3',
                    'os_project': 'admin',
                    'os_user_domain': 'default',
                    'os_project_domain': 'default',
                    }
        self.assertEqual(expected, result)

    def test_create_auth_parameters_env_v2(self):
        self.useFixture(fixtures.EnvironmentVariable('OS_USERNAME', 'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PASSWORD', 'pw'))
        self.useFixture(fixtures.EnvironmentVariable('OS_TENANT_NAME',
                                                     'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_AUTH_URL', 'auth'))
        self.useFixture(fixtures.EnvironmentVariable('OS_PROJECT_NAME',
                                                     'admin'))
        self.useFixture(fixtures.EnvironmentVariable('OS_USER_DOMAIN_ID',
                                                     None))
        self.useFixture(fixtures.EnvironmentVariable('OS_PROJECT_DOMAIN_ID',
                                                     None))
        self.useFixture(fixtures.EnvironmentVariable('OS_USER_DOMAIN_NAME',
                                                     None))
        self.useFixture(fixtures.EnvironmentVariable('OS_PROJECT_DOMAIN_NAME',
                                                     None))
        result = auth._create_auth_parameters()
        expected = {'os_user': 'admin',
                    'os_password': 'pw',
                    'os_tenant': 'admin',
                    'os_auth_url': 'auth',
                    'os_project': 'admin',
                    'os_user_domain': '',
                    'os_project_domain': '',
                    }
        self.assertEqual(expected, result)


V2_TOKEN_DATA = {'token': {'id': 'fake_token'},
                 'serviceCatalog': [{'name': 'nova'},
                                    {'name': 'heat',
                                     'endpoints': [
                                         {'publicURL': 'heat_endpoint'}
                                         ]
                                     }
                                    ]}
V3_TOKEN_DATA = {'auth_token': 'fake_v3_token',
                 'catalog': [{'name': 'nova'},
                             {'name': 'heat',
                              'endpoints': [
                                  {'interface': 'private'},
                                  {'interface': 'public',
                                   'url': 'heat_endpoint'}
                                  ]
                              }
                             ]}


class TestKeystoneAuth(testtools.TestCase):
    @mock.patch('keystoneauth1.session.Session')
    @mock.patch('keystoneauth1.identity.v3.Password')
    def test_get_keystone_session(self, mock_password, mock_session):
        fake_auth_data = {'os_user': 'admin',
                          'os_password': 'password',
                          'os_tenant': 'admin',
                          'os_auth_url': 'auth/v3',
                          'os_project': 'admin',
                          'os_user_domain': 'default',
                          'os_project_domain': 'default',
                          }
        mock_password_auth = mock.Mock()
        mock_password.return_value = mock_password_auth
        auth._get_keystone_session(fake_auth_data)
        mock_password.assert_called_once_with(auth_url='auth/v3',
                                              username='admin',
                                              password='password',
                                              project_name='admin',
                                              user_domain_name='default',
                                              project_domain_name='default'
                                              )
        mock_session.assert_called_once_with(auth=mock_password_auth)

    @mock.patch('keystoneclient.v2_0.client.Client')
    def test_get_keystone_client_v2(self, mock_ksc):
        fake_auth_data = {'os_user': 'admin',
                          'os_password': 'password',
                          'os_tenant': 'admin',
                          'os_auth_url': 'auth',
                          }
        auth._get_keystone_client(fake_auth_data)
        mock_ksc.assert_called_once_with(username='admin', password='password',
                                         tenant_name='admin', auth_url='auth')

    @mock.patch('openstack_virtual_baremetal.auth._get_keystone_session')
    @mock.patch('keystoneclient.v3.client.Client')
    def test_get_keystone_client_v3(self, mock_ksc, mock_gks):
        fake_auth_data = {'os_user': 'admin',
                          'os_password': 'password',
                          'os_tenant': 'admin',
                          'os_auth_url': 'auth/v3',
                          'os_project': 'admin',
                          'os_user_domain': 'default',
                          'os_project_domain': 'default',
                          }
        mock_session = mock.Mock()
        mock_gks.return_value = mock_session
        auth._get_keystone_client(fake_auth_data)
        mock_gks.assert_called_once_with(fake_auth_data)
        mock_ksc.assert_called_once_with(session=mock_session)

    @mock.patch('openstack_virtual_baremetal.auth._get_keystone_client')
    @mock.patch('openstack_virtual_baremetal.auth._create_auth_parameters')
    def test_get_keystone_token_v2(self, mock_cap, mock_gkc):
        fake_auth_data = {'os_user': 'admin',
                          'os_password': 'password',
                          'os_tenant': 'admin',
                          'os_auth_url': 'auth',
                          'os_project': '',
                          'os_user_domain': '',
                          'os_project_domain': '',
                          }
        mock_cap.return_value = fake_auth_data
        mock_client = mock.Mock()
        mock_gkc.return_value = mock_client
        auth._get_keystone_token()
        mock_gkc.assert_called_once_with(fake_auth_data)
        mock_get_token = mock_client.get_raw_token_from_identity_service
        mock_get_token.assert_called_once_with(username='admin',
                                               password='password',
                                               tenant_name='admin',
                                               auth_url='auth'
                                               )

    @mock.patch('openstack_virtual_baremetal.auth._get_keystone_client')
    @mock.patch('openstack_virtual_baremetal.auth._create_auth_parameters')
    def test_get_keystone_token_v3(self, mock_cap, mock_gkc):
        fake_auth_data = {'os_user': 'admin',
                          'os_password': 'password',
                          'os_tenant': '',
                          'os_auth_url': 'auth/v3',
                          'os_project': 'admin',
                          'os_user_domain': 'default',
                          'os_project_domain': 'default',
                          }
        mock_cap.return_value = fake_auth_data
        mock_client = mock.Mock()
        mock_gkc.return_value = mock_client
        auth._get_keystone_token()
        mock_gkc.assert_called_once_with(fake_auth_data)
        mock_get_token = mock_client.get_raw_token_from_identity_service
        mock_get_token.assert_called_once_with(username='admin',
                                               password='password',
                                               project_name='admin',
                                               auth_url='auth/v3',
                                               user_domain_name='default',
                                               project_domain_name='default'
                                               )

    @mock.patch('openstack_virtual_baremetal.auth._get_keystone_token')
    @mock.patch('openstack_virtual_baremetal.auth._create_auth_parameters')
    def test_get_token_and_endpoint_v2(self, mock_cap, mock_gkt):
        fake_auth_data = {'os_user': 'admin',
                          'os_password': 'password',
                          'os_tenant': 'admin',
                          'os_auth_url': 'auth',
                          'os_project': '',
                          'os_user_domain': '',
                          'os_project_domain': '',
                          }
        mock_cap.return_value = fake_auth_data
        mock_gkt.return_value = V2_TOKEN_DATA
        token, endpoint = auth._get_token_and_endpoint('heat')
        self.assertEqual('fake_token', token)
        self.assertEqual('heat_endpoint', endpoint)

    @mock.patch('openstack_virtual_baremetal.auth._get_keystone_token')
    @mock.patch('openstack_virtual_baremetal.auth._create_auth_parameters')
    def test_get_token_and_endpoint_v3(self, mock_cap, mock_gkt):
        fake_auth_data = {'os_user': 'admin',
                          'os_password': 'password',
                          'os_tenant': '',
                          'os_auth_url': 'auth/v3',
                          'os_project': 'admin',
                          'os_user_domain': 'default',
                          'os_project_domain': 'default',
                          }
        mock_cap.return_value = fake_auth_data
        mock_gkt.return_value = V3_TOKEN_DATA
        token, endpoint = auth._get_token_and_endpoint('heat')
        self.assertEqual('fake_v3_token', token)
        self.assertEqual('heat_endpoint', endpoint)

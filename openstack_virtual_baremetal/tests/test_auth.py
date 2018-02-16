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
import json
import mock
import testtools

from openstack_virtual_baremetal import auth


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
                    'os_tenant': 'admin',
                    'os_auth_url': 'auth/v3',
                    'os_project': 'admin',
                    'os_user_domain': 'default',
                    'os_project_domain': 'default',
                    }
        self.assertEqual(expected, result)


class TestCloudJSON(testtools.TestCase):
    @mock.patch('openstack_virtual_baremetal.auth.OS_CLOUD', 'foo')
    @mock.patch('os_client_config.OpenStackConfig')
    def test_cloud_json(self, mock_osc):
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
        result = auth._cloud_json()
        expected = json.dumps(mock_data.config)
        self.assertEqual(expected, result)

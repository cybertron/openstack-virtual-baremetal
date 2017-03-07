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

import os
import sys

from keystoneclient.v2_0 import client as keystone_client
from keystoneclient.v3 import client as keystone_v3_client


def _validate_auth_parameters(username, password, tenant, auth_url,
                              project, user_domain, project_domain):
    if '/v3' not in auth_url:
        if not username or not password or not tenant or not auth_url:
            print('Source an appropriate rc file first')
            sys.exit(1)
    else:
        if (not username or not password or not auth_url or not project or
                not user_domain or not project_domain):
            print('Source an appropriate rc file first')
            sys.exit(1)

def _create_auth_parameters():
    cloud = os.environ.get('OS_CLOUD')
    if cloud:
        import os_client_config
        config = os_client_config.OpenStackConfig().get_one_cloud(cloud)
        auth = config.config['auth']
        username = auth['username']
        password = auth['password']
        # os_client_config seems to always call this project_name
        tenant = auth['project_name']
        auth_url = auth['auth_url']
        project = auth['project_name']
        user_domain = (auth.get('user_domain_name') or
                       auth.get('user_domain_id', ''))
        project_domain = (auth.get('project_domain_name') or
                          auth.get('project_domain_id', ''))

    else:
        username = os.environ.get('OS_USERNAME')
        password = os.environ.get('OS_PASSWORD')
        tenant = os.environ.get('OS_TENANT_NAME', '')
        auth_url = os.environ.get('OS_AUTH_URL', '')
        project = os.environ.get('OS_PROJECT_NAME', '')
        user_domain = (os.environ.get('OS_USER_DOMAIN_ID') or
                       os.environ.get('OS_USER_DOMAIN_NAME', ''))
        project_domain = (os.environ.get('OS_PROJECT_DOMAIN_ID') or
                          os.environ.get('OS_PROJECT_DOMAIN_NAME', ''))
        _validate_auth_parameters(username, password, tenant, auth_url,
                                  project, user_domain, project_domain)
    return {'os_user': username,
            'os_password': password,
            'os_tenant': tenant,
            'os_auth_url': auth_url,
            'os_project': project,
            'os_user_domain': user_domain,
            'os_project_domain': project_domain,
            }


def _get_keystone_session(auth_data):
    username = auth_data['os_user']
    password = auth_data['os_password']
    tenant = auth_data['os_tenant']
    auth_url = auth_data['os_auth_url']
    project = auth_data['os_project']
    user_domain = auth_data['os_user_domain']
    project_domain = auth_data['os_project_domain']
    from keystoneauth1.identity import v3
    from keystoneauth1 import session
    password_auth = v3.Password(auth_url=auth_url,
                                username=username,
                                password=password,
                                project_name=project,
                                user_domain_name=user_domain,
                                project_domain_name=project_domain)
    return session.Session(auth=password_auth)


def _get_keystone_client(auth_data):
    username = auth_data['os_user']
    password = auth_data['os_password']
    tenant = auth_data['os_tenant']
    auth_url = auth_data['os_auth_url']
    if '/v3' not in auth_url:
        return keystone_client.Client(username=username, password=password,
                                      tenant_name=tenant, auth_url=auth_url)
    else:
        sess = _get_keystone_session(auth_data)
        return keystone_v3_client.Client(session=sess)


def _get_keystone_token():
    auth_data = _create_auth_parameters()
    username = auth_data['os_user']
    password = auth_data['os_password']
    tenant = auth_data['os_tenant']
    auth_url = auth_data['os_auth_url']
    project = auth_data['os_project']
    user_domain = auth_data['os_user_domain']
    project_domain = auth_data['os_project_domain']
    kclient = _get_keystone_client(auth_data)
    if '/v3' not in auth_url:
        return kclient.get_raw_token_from_identity_service(username=username,
                                                           password=password,
                                                           tenant_name=tenant,
                                                           auth_url=auth_url)
    else:
        return kclient.get_raw_token_from_identity_service(
            username=username,
            password=password,
            project_name=project,
            auth_url=auth_url,
            user_domain_name=user_domain,
            project_domain_name=project_domain)



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


# Older versions of os-client-config pop this from the environment when
# make_client is called.  Cache it on import so we know what the original
# value was, regardless of any funny business that happens later.
OS_CLOUD = os.environ.get('OS_CLOUD')


def _validate_auth_parameters(username, password, tenant, auth_url,
                              project, user_domain, project_domain):
    """Validate that the necessary auth parameters are set

    Depending on the version of keystone in use, certain parameters are
    required for successful keystone authentication.  If the combination
    passed to this function is not valid, it will print an error message and
    exit with a return code of 1 immediately.
    """
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
    """Read keystone auth parameters from appropriate source

    If the environment variable OS_CLOUD is set, read the auth information
    from os_client_config.  Otherwise, read it from environment variables.
    When reading from the environment, also validate that all of the required
    values are set.

    :returns: A dict containing the following keys: os_user, os_password,
              os_tenant, os_auth_url, os_project, os_user_domain,
              os_project_domain.
    """
    if OS_CLOUD:
        import os_client_config
        config = os_client_config.OpenStackConfig().get_one_cloud(OS_CLOUD)
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
    """Get a new keystone session object

    :param auth_data: Dict of authentication parameters as returned from
    _create_auth_parameters.

    :returns: keystoneclient Session
    """
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
    """Get an instance of keystoneclient.Client

    Abstracts away the version-specific logic of getting a new instance of
    the keystone client.

    :param auth_data: Dict of authentication parameters as returned from
    _create_auth_parameters.

    :returns: A new keystoneclient Client instance
    """
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
    """Get a raw keystone token

    This is a wrapper around the keystoneclient
    get_raw_token_from_identity_service that handles both keystone v2 and v3.

    :returns: Keystone token data structure
    """
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


def _get_token_and_endpoint(name):
    """Return a token id and endpoint url for the specified service

    :param name: The name of the service.  heat, glance, etc.
    :returns: A tuple of (token_id, service_endpoint)
    """
    auth_data = _create_auth_parameters()
    auth_url = auth_data['os_auth_url']
    # Get token for service to use
    if '/v3' not in auth_url:
        token_data = _get_keystone_token()
        token_id = token_data['token']['id']
        catalog_key = 'serviceCatalog'
    else:
        token_data = _get_keystone_token()
        token_id = token_data['auth_token']
        catalog_key = 'catalog'

    # Get service endpoint
    for endpoint in token_data[catalog_key]:
        if endpoint['name'] == name:
            try:
                # TODO: What if there's more than one endpoint?
                service_endpoint = endpoint['endpoints'][0]['publicURL']
            except KeyError:
                # Keystone v3 endpoint data looks different
                service_endpoint = [e for e in endpoint['endpoints']
                                    if e['interface'] == 'public'][0]['url']
    return token_id, service_endpoint

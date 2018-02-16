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

import json
import os

import os_client_config


# Older versions of os-client-config pop this from the environment when
# make_client is called.  Cache it on import so we know what the original
# value was, regardless of any funny business that happens later.
OS_CLOUD = os.environ.get('OS_CLOUD')


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

    return {'os_user': username,
            'os_password': password,
            'os_tenant': tenant,
            'os_auth_url': auth_url,
            'os_project': project,
            'os_user_domain': user_domain,
            'os_project_domain': project_domain,
            }


def _cloud_json():
    """Return the current cloud's data in JSON

    Retrieves the cloud from os-client-config and serializes it to JSON.
    """
    config = os_client_config.OpenStackConfig().get_one_cloud(OS_CLOUD)
    return json.dumps(config.config)

#!/bin/bash
set -x

# Also python-crypto, but that requires special handling because we used to
# install python2-crypto from EPEL
# python-[nova|neutron]client are in a similar situation.  They were renamed
# in RDO to python2-*
required_packages="python-pip os-net-config git jq"

function have_packages() {
    for i in $required_packages; do
        if ! rpm -qa | grep -q $i; then
            return 1
        fi
    done
    if ! (rpm -qa | egrep -q "python-crypto|python2-crypto"); then
        return 1
    fi
    if ! (rpm -qa | egrep -q "python-novaclient|python2-novaclient"); then
        return 1
    fi
    if ! (rpm -qa | egrep -q "python-neutronclient|python2-neutronclient"); then
        return 1
    fi
    if ! pip freeze | grep -q pyghmi; then
        return 1
    fi
    return 0
}

if ! have_packages; then
    yum -y update centos-release # required for rdo-release install to work
    yum install -y https://rdo.fedorapeople.org/rdo-release.rpm
    yum install -y $required_packages python-crypto python2-novaclient python2-neutronclient
    pip install pyghmi
fi

cat <<EOF >/usr/local/bin/openstackbmc
$openstackbmc_script
EOF
chmod +x /usr/local/bin/openstackbmc

export OS_USERNAME=$os_user
export OS_TENANT_NAME=$os_tenant
export OS_PASSWORD=$os_password
export OS_AUTH_URL=$os_auth_url
export OS_PROJECT_NAME=$os_project
# NOTE(bnemec): The double _ in these names is intentional.  It prevents
# collisions with the $os_user and $os_project values above.
export OS_USER_DOMAIN_ID=$os__user_domain
export OS_PROJECT_DOMAIN_ID=$os__project_domain

# Following is required so that openstack CLIs work with DOMAIN_NAME credentials
export OS_USER_DOMAIN_NAME=$os__user_domain
export OS_PROJECT_DOMAIN_NAME=$os__project_domain

# v3 env vars mess up v2 auth
[ -z $OS_PROJECT_NAME ] && unset OS_PROJECT_NAME
[ -z $OS_USER_DOMAIN_ID ] && unset OS_USER_DOMAIN_ID
[ -z $OS_PROJECT_DOMAIN_ID ] && unset OS_PROJECT_DOMAIN_ID
[ -z $OS_USER_DOMAIN_NAME ] && unset OS_USER_DOMAIN_NAME
[ -z $OS_PROJECT_DOMAIN_NAME ] && unset OS_PROJECT_DOMAIN_NAME
# Check if v3 DOMAIN_ID credential works
if ! neutron net-list; then
	# unset DOMAIN_ID variables, this makes use of DOMAIN_NAME variables
	unset OS_PROJECT_DOMAIN_ID; unset OS_USER_DOMAIN_ID
fi
# At some point neutronclient started returning a python list repr from this
# command instead of just the value.  This sed will strip off the bits we
# don't care about without messing up the output from older clients.
private_subnet=$(neutron net-show -f value -c subnets $private_net | sed "s/\[u'\(.*\)'\]/\1/")
default_gw=$(neutron subnet-show $private_subnet -f value -c gateway_ip)
prefix_len=$(neutron subnet-show -f value -c cidr $private_subnet | awk -F / '{print $2}')
cache_status=
if [ "$bmc_use_cache" != "False" ]; then
    cache_status="--cache-status"
fi

mkdir /etc/os-net-config
echo "network_config:" > /etc/os-net-config/config.yaml
echo "  -" >> /etc/os-net-config/config.yaml
echo "    type: interface" >> /etc/os-net-config/config.yaml
echo "    name: eth0" >> /etc/os-net-config/config.yaml
echo "    use_dhcp: false" >> /etc/os-net-config/config.yaml
echo "    mtu: 1450" >> /etc/os-net-config/config.yaml
echo "    routes:" >> /etc/os-net-config/config.yaml
echo "      - default: true" >> /etc/os-net-config/config.yaml
echo "        next_hop: $default_gw" >> /etc/os-net-config/config.yaml
echo "    addresses:" >> /etc/os-net-config/config.yaml
echo "    - ip_netmask: $bmc_utility/$prefix_len" >> /etc/os-net-config/config.yaml

cat <<EOF >/usr/lib/systemd/system/config-bmc-ips.service
[Unit]
Description=config-bmc-ips Service
Requires=network.target
After=network.target

[Service]
ExecStart=/bin/os-net-config --verbose
Type=oneshot
User=root
StandardOutput=kmsg+console
StandardError=inherit

[Install]
WantedBy=multi-user.target
EOF

for i in $(seq 1 $bm_node_count)
do
    bm_port="$bm_prefix_$(($i-1))"
    bm_instance=$(neutron port-show $bm_port -c device_id -f value)
    bmc_port="$bmc_prefix_$(($i-1))"
    bmc_ip=$(neutron port-show $bmc_port -c fixed_ips -f value | jq -r .ip_address)
    # Newer neutronclient requires explicit json output and a slightly
    # different jq query
    if [ -z "$bmc_ip" ]; then
        bmc_ip=$(neutron port-show $bmc_port -c fixed_ips -f json | jq -r .fixed_ips[0].ip_address)
    fi
    unit="openstack-bmc-$bm_port.service"

    cat <<EOF >/usr/lib/systemd/system/$unit
[Unit]
Description=openstack-bmc $bm_port Service
Requires=config-bmc-ips.service
After=config-bmc-ips.service

[Service]
ExecStart=/usr/local/bin/openstackbmc  --os-user $os_user --os-password $os_password --os-tenant "$os_tenant" --os-auth-url $os_auth_url --os-project "$os_project" --os-user-domain "$os__user_domain" --os-project-domain "$os__project_domain" --instance $bm_instance --address $bmc_ip $cache_status
Restart=always

User=root
StandardOutput=kmsg+console
StandardError=inherit

[Install]
WantedBy=multi-user.target
EOF

    echo "    - ip_netmask: $bmc_ip/$prefix_len" >> /etc/os-net-config/config.yaml
done

# It will be automatically started because the bmc services depend on it,
# but to avoid confusion also explicitly enable it.
systemctl enable config-bmc-ips

for i in $(seq 1 $bm_node_count)
do
    bm_port="$bm_prefix_$(($i-1))"
    unit="openstack-bmc-$bm_port.service"
    systemctl enable $unit
    systemctl start $unit
    systemctl status $unit
done


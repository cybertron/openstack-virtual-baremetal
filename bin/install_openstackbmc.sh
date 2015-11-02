#!/bin/bash
set -x

yum -y update centos-release # required for rdo-release install to work
yum install -y https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm
yum install -y https://rdo.fedorapeople.org/rdo-release.rpm
yum install -y python-pip python-crypto os-net-config python-novaclient python-neutronclient git jq
pip install --no-deps git+https://github.com/steveb/pyghmi.git@custom-bind-address

cat <<EOF >/usr/local/bin/openstackbmc
$openstackbmc_script
EOF
chmod +x /usr/local/bin/openstackbmc

mkdir /etc/os-net-config
echo "network_config:" > /etc/os-net-config/config.yaml

for i in $(seq 2 $bm_node_count)
do
    nic="eth$(($i-1))"
    echo "- {name: $nic, type: interface, use_dhcp: true, defroute: no}" >> /etc/os-net-config/config.yaml
done
os-net-config --verbose

export OS_USERNAME=$os_user
export OS_TENANT_NAME=$os_tenant
export OS_PASSWORD=$os_password
export OS_AUTH_URL=$os_auth_url

for i in $(seq 1 $bm_node_count)
do
    bm_port="$bm_prefix_$(($i-1))"
    bm_instance=$(neutron port-show $bm_port -c device_id -f value)
    bmc_port="$bmc_prefix_$(($i-1))"
    bmc_ip=$(neutron port-show $bmc_port -c fixed_ips -f value | jq -r .ip_address)
    unit="openstack-bmc-$bm_port.service"

    cat <<EOF >/usr/lib/systemd/system/$unit
[Unit]
Description=openstack-bmc Service

[Service]
ExecStart=/usr/local/bin/openstackbmc  --os-user $os_user --os-password $os_password --os-tenant $os_tenant --os-auth-url $os_auth_url --instance $bm_instance --address $bmc_ip

User=root
StandardOutput=kmsg+console
StandardError=inherit

[Install]
WantedBy=multi-user.target
Alias=openstack-bmc.service
EOF

    systemctl enable $unit
    systemctl start $unit
    systemctl status $unit
done


Configuring the Host Cloud
==========================

Some of the configuration recommended below is optional, but applying
all of it will provide the optimal experience.

The changes described in this document apply to compute nodes in the
host cloud.

#. Neutron must be configured to use the NoopFirewallDriver.  Edit
   ``/etc/neutron/plugins/ml2/ml2_conf.ini`` and set the option
   ``firewall_driver`` in the ``[securitygroup]`` section as follows::

       firewall_driver = neutron.agent.firewall.NoopFirewallDriver

#. In Liberty and later versions, arp spoofing must be disabled.  Edit
   ``/etc/neutron/plugins/ml2/ml2_conf.ini`` and set the option
   ``prevent_arp_spoofing`` in the ``[agent]`` section as follows::

        prevent_arp_spoofing = False

#. The Nova option ``force_config_drive`` must _not_ be set.

#. Ideally, jumbo frames should be enabled on the host cloud.  This
   avoids MTU problems when deploying to instances over tunneled
   Neutron networks with VXLAN or GRE.

   For TripleO-based host clouds, this can be done by setting ``mtu``
   on all interfaces and vlans in the network isolation nic-configs.
   A value of at least 1550 should be sufficient to avoid problems.

   If this cannot be done (perhaps because you don't have access to make
   such a change on the host cloud), it will likely be necessary to
   configure a smaller MTU on the deployed virtual instances.  For a
   TripleO undercloud, Neutron should be configured to advertise a
   smaller MTU to instances.  Run the following as root::

       # Replace 'eth1' with the actual device to be used for the
       # provisioning network
       ip link set eth1 mtu 1350
       echo -e "\ndhcp-option-force=26,1350" >> /etc/dnsmasq-ironic.conf
       systemctl restart 'neutron-*'

   If network isolation is in use, the templates must also configure
   mtu as discussed above, except the mtu should be set to 1350 instead
   of 1550.

#. Restart ``nova-compute`` and ``neutron-openvswitch-agent`` to apply the
   changes above.

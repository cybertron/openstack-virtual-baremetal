Deploying with QuintupleO
=========================

QuintupleO is short for OpenStack on OpenStack on OpenStack.  It was the
original name for OVB, and has been repurposed to indicate that this
deployment method is able to deploy a full TripleO development environment
in one command.  It should be useful for non-TripleO users of OVB as well,
however.

#. Copy the example env file and edit it to reflect the host environment::

      cp environments/base.yaml env.yaml
      vi env.yaml

#. Deploy a QuintupleO stack.  The example command includes a number of
   environment files intended to simplify the deployment process or make
   it compatible with a broader set of host clouds.  However, these
   environments are not necessary in every situation and may not even work
   with some older clouds.  See below for details on customizing an OVB
   deployment for your particular situation::

    bin/deploy.py --quintupleo -e env.yaml -e environments/all-networks-port-security.yaml -e environments/create-private-network.yaml

   .. note:: There is a quintupleo-specific option ``--id`` in deploy.py.
             It appends the value passed in to the name of all resources
             in the stack.  For example, if ``undercloud_name`` is set to
             'undercloud' and ``--id foo`` is passed to deploy.py, the
             resulting undercloud VM will be named 'undercloud-foo'.  It is
             recommended that this be used any time multiple environments are
             being deployed in the same cloud/tenant to avoid name collisions.

             Be aware that when ``--id`` is used, a new environment file will
             be generated that reflects the new names.  The name of the new
             file will be ``env-${id}.yaml``.  This new file should be passed
             to build-nodes-json instead of the original.

   .. note:: See :ref:`advanced-options` for other ways to customize an OVB
             deployment.

#. Wait for Heat stack to complete.  To make this easier, the ``--poll``
   option can be passed to ``deploy.py``.

   .. note:: The BMC instance does post-deployment configuration that can
             take a while to complete, so the Heat stack completing does
             not necessarily mean the environment is entirely ready for
             use.  To determine whether the BMC is finished starting up,
             run ``nova console-log bmc``.  The BMC service outputs a
             message like "Managing instance [uuid]" when it is fully
             configured.  There should be one of these messages for each
             baremetal instance.

   ::

      heat stack-show quintupleo

#. Build a nodes.json file that can be imported into Ironic::

    bin/build-nodes-json
    scp nodes.json centos@[undercloud floating ip]:~/instackenv.json

   .. note:: Only the base environment file needs to be passed to this command.
             Additional option environments that may have been passed to the
             deploy command should *not* be included here.

   .. note:: If ``--id`` was used to deploy the stack, make sure to pass the
             generated ``env-${id}.yaml`` file to build-nodes-json using the
             ``--env`` parameter.  Example::

                bin/build-nodes-json --env env-foo.yaml

   .. note:: If roles were used for the deployment, separate node files named
             ``nodes-<profile>.json`` will also be output that list only the
             nodes for that particular profile.  Nodes with no profile
             specified will go in ``nodes-no-profile.json``.  The base
             ``nodes.json`` will still contain all of the nodes in the
             deployment, regardless of profile.

   .. note:: ``build-nodes-json`` also outputs a file named ``bmc_bm_pairs``
             that lists which BMC address corresponds to a given baremetal
             instance.

Deleting an OVB Environment
---------------------------

All of the OpenStack resources created by OVB are part of the Heat stack, so
to delete the environment just delete the Heat stack.  There are a few local
files that may also have been created as part of the deployment, such as
ID environment files, nodes.json files, and bmc_bm_pairs.  Once the stack is
deleted these can be removed safely as well.

.. _advanced-options:

Advanced Options
----------------

There are also a number of advanced options that can be enabled for a
QuintupleO deployment.  For each such option there is a sample environment
to be passed to the deploy command.

For example, to deploy using the Neutron port-security extension to allow
DHCP and PXE booting, the following command could be used::

    bin/deploy.py --quintupleo -e env.yaml -e environments/port-security.yaml

.. important:: When deploying with multiple environment files, ``env.yaml``
               *must* be explicitly passed to the deploy command.
               ``deploy.py`` will only default to using ``env.yaml`` if no
               environments are specified.

Some options may have additional configuration parameters.  These parameters
will be listed in the environment file.

A full list of the option environments available can be found at
:doc:`environment-index`.

Network Isolation
-----------------

There are a number of environments related to enabling the network isolation
functionality in OVB.  These environments are named ``all-networks*.yaml``
and cause OVB to deploy additional network interfaces on the baremetal
instances that allow the use of TripleO's network isolation.

.. note:: There are templates suitable for doing a TripleO overcloud deployment
          with network isolation in the ``overcloud-templates`` directory.  See
          the readme files in those directories for details on how to use them.

          The v2 versions of the templates are suitable for use with the
          TripleO Ocata release and later.  The others can be used in Newton
          and earlier.

Three primary networking layouts are included:

* Basic.  This is the default and will only deploy a provisioning interface to
  the baremetal nodes.  It is not suitable for use with network isolation.

* All Networks.  This will deploy an interface per isolated network to the
  baremetal instances.  It is suitable for use with any of the overcloud
  network isolation templates not starting with 'bond'.

* All Networks, Public Bond.  This will also deploy an interface per isolated
  network to the baremetal instances, but it will additionally deploy a second
  interface for the 'public' network that can be used to test bonding in an
  OVB environment.  The ``bond-*`` overcloud templates must be used with this
  type of environment.

Each of the networking layouts has two variations: with and without the use of
Neutron's port-security extension.  The reason for this is that older releases
of OpenStack did not support port-security, so those templates cannot be used.
However, use of the port-security extension allows OVB to work on a much larger
number of clouds because it does not require insecure Neutron settings.

While the port-security extension existed as far back as the Liberty release,
it has only been successfully tested with OVB on Newton and above.

The port-security environments can be recognized by the presence of
`port-security` somewhere in the filename.  Network environments without that
substring are the standard ones that require the noop Neutron firewall driver.

QuintupleO and routed networks
------------------------------

TripleO supports deploying OpenStack with nodes on multiple network segments
which is connected via L3 routing. OVB can set up a full development
environment with routers and DHCP-relay service.  This environment is targeted
for TripleO development, however it should be useful for non-TripleO users of
OVB as well.

#. When deploying QuintupleO with routed networks environment files to enable
   routed networks must be included, as well as one or more role environment
   files. See :ref:`Enable Routed Networks`,
   :ref:`Configuration for Routed Networks`, and
   :ref:`Base Role Configuration for Routed Networks` in the
   :doc:`environment-index` for details.

#. Copy the example env file and edit it to reflect the host environment::

      cp environments/base.yaml env.yaml
      vi env.yaml

#. Copy the ``routed-networks-configuration.yaml`` sample environment file and
   edit it to reflect the host environment::

     cp environments/routed-networks-configuration.yaml env-routed-networks.yaml
     vi env-routed-networks.yaml

#. For each desired role, copy the ``routed-networks-role.yaml`` sample
   environment file and edit it to reflect the host environment::

     cp environments/routed-networks-role.yaml env-leaf1.yaml
     vi env-leaf1.yaml

#. Deploy the QuintupleO routed networks environment by running the deploy.py
   command. For example::

     ./bin/deploy.py --env env.yaml \
                     --quintupleo \
                     --env environments/all-networks-port-security.yaml \
                     --env environments/routed-networks.yaml \
                     --env env-routed-networks.yaml \
                     --role env-leaf1.yaml

#. When generating the ``nodes.json`` file for TripleO undercloud node import,
   the environment ``env-routed.yaml`` should be specified. Also, to include
   physical network attributes of the node ports in ``nodes.json`` specify the
   ``--physical_network`` option when running ``build-nodes-json``. For
   example::

     bin/build-nodes-json --physical_network

   The following is an example node definition produced when using the
   ``--physical_network`` options. Notice that ports are defined with both
   ``address`` and ``physical_network`` attributes.

   ::

     {
       "pm_password": "password",
       "name": "baremetal-leaf1-0",
       "memory": 8192,
       "pm_addr": "10.0.1.13",
       "ports": [
         {
           "physical_network": "provision2",
           "address": "fa:16:3e:2f:a1:cf"
         }
       ],
       "capabilities": "boot_option:local,profile:leaf1",
       "pm_type": "pxe_ipmitool",
       "disk": 80,
       "arch": "x86_64",
       "cpu": 4,
       "pm_user": "admin"
     }

    .. NOTE:: Due to technical debet (backward compatibility) the TripleO
              Undercloud uses ``ctlplane`` as the physical network name for the
              subnet that is local to the Undercloud itself. Either override
              the name of the provision network in the ovb environment by
              setting: ``provision_net: ctlplane`` in the
              ``parameters_defaults`` section or edit the generated nodes.json
              file, replacing:
              ``"physical_network": "<name-used-for-provision_net>"`` with
              ``"physical_network": "ctlplane"``.

#. For convenience router addresses are made available via the
   ``network_environment_data`` key in the stack output of the quintupleo heat
   stack. To retrieve this data run the ``openstack stack show`` command. For
   example::

     $ openstack stack show quintupleo -c outputs -f yaml

     outputs:
     - description: floating ip of the undercloud instance
       output_key: undercloud_host_floating_ip
       output_value: 38.145.35.98
     - description: Network environment data, router addresses etc.
       output_key: network_environment_data
       output_value:
         internal2_router: 172.17.1.204
         internal_router_address: 172.17.0.201
         provision2_router: 192.168.25.254
         provision3_router: 192.168.26.254
         provision_router: 192.168.24.254
         storage2_router_address: 172.18.1.254
         storage_mgmt2_router_address: 172.19.1.254
         storage_mgmt_router_address: 172.19.0.254
         storage_router_address: 172.18.0.254
         tenant2_router_address: 172.16.1.254
         tenant_router_address: 172.16.0.254
     - description: ip of the undercloud instance on the private network
       output_key: undercloud_host_private_ip
       output_value: 10.0.1.14

#. Below is an example TripleO Undercloud configuration (``undercloud.conf``)
   with routed networks support enabled and the three provisioning networks
   defined.

   ::

     [DEFAULT]
     enable_routed_networks = true
     enable_ui = false
     overcloud_domain_name = localdomain
     scheduler_max_attempts = 2
     undercloud_ntp_servers = pool.ntp.org
     undercloud_hostname = undercloud.rdocloud
     local_interface = eth1
     local_mtu = 1450
     local_ip = 192.168.24.1/24
     undercloud_public_host = 192.168.24.2
     undercloud_admin_host = 192.168.24.3
     undercloud_nameservers = 8.8.8.8,8.8.4.4
     local_subnet = provision
     subnets = provision,provision2,provision3

     [provision]
     cidr = 192.168.24.0/24
     dhcp_start = 192.168.24.10
     dhcp_end = 192.168.24.30
     gateway = 192.168.24.254
     inspection_iprange = 192.168.24.100,192.168.24.120
     masquerade = true

     [provision2]
     cidr = 192.168.25.0/24
     dhcp_start = 192.168.25.10
     dhcp_end = 192.168.25.30
     gateway = 192.168.25.254
     inspection_iprange = 192.168.25.100,192.168.25.120
     masquerade = true

     [provision3]
     cidr = 192.168.26.0/24
     dhcp_start = 192.168.26.10
     dhcp_end = 192.168.26.30
     gateway = 192.168.26.254
     inspection_iprange = 192.168.26.100,192.168.26.120
     masquerade = true

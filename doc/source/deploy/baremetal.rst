Deploying a Standalone Baremetal Stack
======================================

The process described here will create a very minimal OVB environment, and the
user will be responsible for creating most of the resources manually.  In most
cases it will be easier to use the :doc:`QuintupleO <quintupleo>` deployment
method, which creates most of the resources needed automatically.

#. Create private network.

   If your cloud provider has already created a private network for your use
   then you can skip this step and reference the existing network in your
   OVB environment file.

   ::

      neutron net-create private
      neutron subnet-create --name private private 10.0.1.0/24 --dns-nameserver 8.8.8.8

   You will also need to create a router so traffic from your private network
   can get to the external network.  The external network should have been
   created by the cloud provider::

      neutron router-create router
      neutron router-gateway-set router [external network name or id]
      neutron router-interface-add router private

#. Create provisioning network.

   .. note:: The CIDR used for the subnet does not matter.
             Standard tenant and external networks are also needed to
             provide floating ip access to the undercloud and bmc instances

   .. warning:: Do not enable DHCP on this network.  Addresses will be
                assigned by the undercloud Neutron.

   ::

      neutron net-create provision
      neutron subnet-create --name provision --no-gateway --disable-dhcp provision 192.168.24.0/24

#. Create "public" network.

   .. note:: The CIDR used for the subnet does not matter.
             This can be used as the network for the public API endpoints
             on the overcloud, but it does not have to be accessible
             externally.  Only the undercloud VM will need to have access
             to this network.

   .. warning:: Do not enable DHCP on this network.  Doing so may cause
                conflicts between the host cloud metadata service and the
                undercloud metadata service.  Overcloud nodes will be
                assigned addresses on this network by the undercloud Neutron.

   ::

       neutron net-create public
       neutron subnet-create --name public --no-gateway --disable-dhcp public 10.0.0.0/24

#. Copy the example env file and edit it to reflect the host environment:

   .. note:: Some of the parameters in the base environment file are only
             used for QuintupleO deployments.  Their values will be ignored
             in a plain virtual-baremetal deployment.

   ::

    cp environments/base.yaml env.yaml
    vi env.yaml

#. Deploy the stack::

    bin/deploy.py

#. Wait for Heat stack to complete:

   .. note:: The BMC instance does post-deployment configuration that can
             take a while to complete, so the Heat stack completing does
             not necessarily mean the environment is entirely ready for
             use.  To determine whether the BMC is finished starting up,
             run ``nova console-log bmc``.  The BMC service outputs a
             message like "Managing instance [uuid]" when it is fully
             configured.  There should be one of these messages for each
             baremetal instance.

   ::

      heat stack-show baremetal

#. Boot a VM to serve as the undercloud::

    nova boot undercloud --flavor m1.xlarge --image centos7 --nic net-id=[tenant net uuid] --nic net-id=[provisioning net uuid]
    neutron floatingip-create [external net uuid]
    neutron port-list
    neutron floatingip-associate [floatingip uuid] [undercloud instance port id]

#. Turn off port-security on the undercloud provisioning port::

    neutron port-update [UUID of undercloud port on the provision network] --no-security-groups --port-security-enabled=False

#. Build a nodes.json file that can be imported into Ironic::

    bin/build-nodes-json
    scp nodes.json centos@[undercloud floating ip]:~/instackenv.json

   .. note:: ``build-nodes-json`` also outputs a file named ``bmc_bm_pairs``
             that lists which BMC address corresponds to a given baremetal
             instance.

#. The undercloud vm can now be used with something like TripleO
   to do a baremetal-style deployment to the virtual baremetal instances
   deployed previously.

Deleting an OVB Environment
---------------------------

All of the OpenStack resources created by OVB are part of the Heat stack, so
to delete the environment just delete the Heat stack.  There are a few local
files that may also have been created as part of the deployment, such as
nodes.json files and bmc_bm_pairs.  Once the stack is deleted these can be
removed safely as well.

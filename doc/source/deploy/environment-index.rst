Sample Environment Index
========================

Deploy with All Networks Enabled
--------------------------------

**File:** environments/all-networks-port-security.yaml

**Description:** Deploy an OVB stack that adds interfaces for all the standard TripleO
network isolation networks.  This version uses the port-security
Neutron extension to allow OVB to be run on clouds with security
groups enabled.


Deploy with All Networks Enabled and Two Public Interfaces
----------------------------------------------------------

**File:** environments/all-networks-public-bond-port-security.yaml

**Description:** Deploy an OVB stack that adds interfaces for all the standard TripleO
network isolation networks.  This version will deploy duplicate
public network interfaces on the baremetal instances so that the
public network can be configured as a bond.  It will also use the
port-security Neutron extension to allow OVB to be run on clouds with
security groups enabled.


Deploy with All Networks Enabled and Two Public Interfaces
----------------------------------------------------------

**File:** environments/all-networks-public-bond.yaml

**Description:** Deploy an OVB stack that adds interfaces for all the standard TripleO
network isolation networks.  This version will deploy duplicate
public network interfaces on the baremetal instances so that the
public network can be configured as a bond.


Deploy with All Networks Enabled
--------------------------------

**File:** environments/all-networks.yaml

**Description:** Deploy an OVB stack that adds interfaces for all the standard TripleO
network isolation networks.


Base Configuration Options for Extra Nodes
------------------------------------------

**File:** environments/base-extra-node.yaml

**Description:** Configuration options that need to be set when deploying an OVB
environment with extra undercloud-like nodes.  This environment
should be used like a role file, but will deploy an undercloud-like
node instead of more baremetal nodes.


Base Configuration Options for Secondary Roles
----------------------------------------------

**File:** environments/base-role.yaml

**Description:** Configuration options that need to be set when deploying an OVB
environment that has multiple roles.


Base Configuration Options
--------------------------

**File:** environments/base.yaml

**Description:** Basic configuration options needed for all OVB environments

Enable Instance Status Caching in BMC
-------------------------------------

**File:** environments/bmc-use-cache.yaml

**Description:** Enable caching of instance status in the BMC.  This should reduce load on
the host cloud, but at the cost of potential inconsistency if the state
of a baremetal instance is changed without using the BMC.


Boot Baremetal Instances from Volume
------------------------------------

**File:** environments/boot-baremetal-from-volume.yaml

**Description:** Boot the baremetal instances from Cinder volumes instead of
ephemeral storage.


Boot Undercloud and Baremetal Instances from Volume
---------------------------------------------------

**File:** environments/boot-from-volume.yaml

**Description:** Boot the undercloud and baremetal instances from Cinder volumes instead of
ephemeral storage.


Boot Undercloud Instance from Volume
------------------------------------

**File:** environments/boot-undercloud-from-volume.yaml

**Description:** Boot the undercloud instance from a Cinder volume instead of
ephemeral storage.


Create a Private Network
------------------------

**File:** environments/create-private-network.yaml

**Description:** Create the private network as part of the OVB stack instead of using an
existing one.


Deploy a Basic OVB Environment Using Neutron port-security
----------------------------------------------------------

**File:** environments/port-security.yaml

**Description:** Deploy an OVB stack that uses the Neutron port-security extension to
allow OVB functionality in clouds with security groups enabled.


Disable the Undercloud in a QuintupleO Stack
--------------------------------------------

**File:** environments/quintupleo-no-undercloud.yaml

**Description:** Deploy a QuintupleO environment, but do not create the undercloud
instance.


Configuration for Routed Networks
---------------------------------

**File:** environments/routed-networks-configuration.yaml

**Description:** Contains the available parameters that need to be configured when using
a routed networks environment. Requires the routed-networks.yaml
environment.


Base Role Configuration for Routed Networks
-------------------------------------------

**File:** environments/routed-networks-role.yaml

**Description:** A base role environment that contains the necessary parameters for
deploying with routed networks.


Enable Routed Networks
----------------------

**File:** environments/routed-networks.yaml

**Description:** Enable use of routed networks, where there may be multiple separate
networks connected with a router and DHCP relay. Do not pass any other
network configuration environments after this one or they may override
the changes made by this environment. When this environment is in use,
the routed-networks-configuration environment should usually be
included as well.


Assign the Undercloud an Existing Floating IP
---------------------------------------------

**File:** environments/undercloud-floating-existing.yaml

**Description:** When deploying the undercloud, assign it an existing floating IP instead
of creating a new one.


Do Not Assign a Floating IP to the Undercloud
---------------------------------------------

**File:** environments/undercloud-floating-none.yaml

**Description:** When deploying the undercloud, do not assign a floating ip to it.



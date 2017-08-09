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


Base Configuration Options for Secondary Roles
----------------------------------------------

**File:** environments/base-role.yaml

**Description:** Configuration options that need to be set when deploying an OVB
environment that has multiple roles.


Base Configuration Options
--------------------------

**File:** environments/base.yaml

**Description:** Basic configuration options needed for all OVB environments

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


Assign the Undercloud an Existing Floating IP
---------------------------------------------

**File:** environments/undercloud-floating-existing.yaml

**Description:** When deploying the undercloud, assign it an existing floating IP instead
of creating a new one.


Do Not Assign a Floating IP to the Undercloud
---------------------------------------------

**File:** environments/undercloud-floating-none.yaml

**Description:** When deploying the undercloud, do not assign a floating ip to it.



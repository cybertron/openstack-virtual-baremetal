Using a Deployed OVB Environment
================================

After an OVB environment has been deployed, there are a few things to know.

#. The undercloud vm can be used with something like TripleO
   to do a baremetal-style deployment to the virtual baremetal instances
   deployed previously.

#. If using the full network isolation provided by OS::OVB::BaremetalNetworks
   then a TripleO overcloud can be deployed in the OVB environment by using
   the network templates in the ``network-templates`` (for ipv4) or
   ``ipv6-network-templates`` (for ipv6) directories.

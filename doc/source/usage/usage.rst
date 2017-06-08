Using a Deployed OVB Environment
================================

After an OVB environment has been deployed, there are a few things to know.

#. The undercloud vm can be used with something like TripleO
   to do a baremetal-style deployment to the virtual baremetal instances
   deployed previously.

#. To reset the environment, usually it is sufficient to do a ``nova rebuild``
   on the undercloud to return it to the original image.  To ensure that
   no traces of the old environment remain, the baremetal vms can be rebuilt
   to the ipxe-boot image as well.

   .. note:: If you are relying on the ipxe-boot image to provide PXE boot
             support in your cloud because Nova does not know how to PXE boot
             natively, the baremetal instances must always be rebuilt before
             subsequent deployments.

   .. note:: **Do not** rebuild the bmc.  It is unnecessary and not guaranteed
             to work.

#. If using the full network isolation provided by OS::OVB::BaremetalNetworks
   then a TripleO overcloud can be deployed in the OVB environment by using
   the network templates in the ``network-templates`` (for ipv4) or
   ``ipv6-network-templates`` (for ipv6) directories.

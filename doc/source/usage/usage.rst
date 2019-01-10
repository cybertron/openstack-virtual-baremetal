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

#. If the host cloud's tenant network MTU is 1500 or less, it will be necessary
   to configure the deployed interfaces with a smaller MTU.  The tenant network
   MTU minus 50 is usually a safe value.  For the undercloud this can be done
   by setting ``local_mtu`` in ``undercloud.conf``.

   .. note::
      In Mitaka and older versions of TripleO it will be necessary to do the
      MTU configuration manually.  That can be done with the following
      commands (as root)::

          # Replace 'eth1' with the actual device to be used for the
          # provisioning network
          ip link set eth1 mtu 1350
          echo -e "\ndhcp-option-force=26,1350" >> /etc/dnsmasq-ironic.conf
          systemctl restart 'neutron-*'

#. If using the full network isolation provided by one of the
   ``all-networks*.yaml`` environments then a TripleO overcloud can be deployed
   in the OVB environment by using the network templates in the
   ``overcloud-templates`` directory.  The names are fairly descriptive, but
   this is a brief explanation of each:

   - **network-templates:** IPv4 multi-nic.  Usable with the network layout
     deployed by the ``all-networks.yaml`` environment.
   - **ipv6-network-templates:** IPv6 multi-nic. Usable with the network layout
     deployed by the ``all-networks.yaml`` environment.
   - **bond-network-templates:** IPv4 multi-nic, with duplicate `public`
     interfaces for testing bonded nics.  Usable with the network layout
     deployed by the ``all-networks-public-bond.yaml`` environment.

   The undercloud's ``public`` interface should be configured with the address
   of the default route from the templates in use.  Firewall rules for
   forwarding the traffic from that interface should also be added.  The
   following commands will make the necessary configuration::

      cat >> /tmp/eth2.cfg <<EOF_CAT
      network_config:
        - type: interface
          name: eth2
          use_dhcp: false
          addresses:
            - ip_netmask: 10.0.0.1/24
            - ip_netmask: 2001:db8:fd00:1000::1/64
      EOF_CAT
      sudo os-net-config -c /tmp/eth2.cfg -v
      sudo iptables -A POSTROUTING -s 10.0.0.0/24 ! -d 10.0.0.0/24 -j MASQUERADE -t nat

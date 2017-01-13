Preparing the Host Cloud Environment
------------------------------------

#. Source an rc file that will provide admin credentials for the host cloud.

#. Upload an ipxe-boot image for the baremetal instances::

    glance image-create --name ipxe-boot --disk-format qcow2 --property os_shutdown_timeout=5 --container-format bare < ipxe/ipxe-boot.qcow2

   .. note:: The path provided to ipxe-boot.qcow2 is relative to the root of
             the OVB repo.  If the command is run from a different working
             directory, the path will need to be adjusted accordingly.

   .. note:: os_shutdown_timeout=5 is to avoid server shutdown delays since
             since these servers won't respond to graceful shutdown requests.

   .. note:: On a UEFI enabled openstack cloud, to boot the baremetal instances
             with uefi (instead of the default bios firmware) the image should
             be created with the parameters --property="hw_firmware_type=uefi".

#. Upload a CentOS 7 image for use as the base image::

    wget http://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2

    glance image-create --name CentOS-7-x86_64-GenericCloud --disk-format qcow2 --container-format bare < CentOS-7-x86_64-GenericCloud.qcow2

#. (Optional) Create a pre-populated base BMC image.  This is a CentOS 7 image
   with the required packages for the BMC pre-installed.  This eliminates one
   potential point of failure during the deployment of an OVB environment
   because the BMC will not require any external network resources::

    wget https://repos.fedorapeople.org/repos/openstack-m/ovb/bmc-base.qcow2

    glance image-create --name bmc-base --disk-format qcow2 --container-format bare < bmc-base.qcow2

   To use this image, configure ``bmc_image`` in env.yaml to be ``bmc-base`` instead
   of the generic CentOS 7 image.

#. Create recommended flavors::

    nova flavor-create baremetal auto 6144 50 2
    nova flavor-create bmc auto 512 20 1

   These flavors can be customized if desired.  For large environments
   with many baremetal instances it may be wise to give the bmc flavor
   more memory.  A 512 MB BMC will run out of memory around 20 baremetal
   instances.

#. Source an rc file that will provide user credentials for the host cloud.

#. Add a Nova keypair to be injected into instances::

    nova keypair-add --pub-key ~/.ssh/id_rsa.pub default

#. (Optional) Configure quotas.  When running in a dedicated OVB cloud, it may
   be helpful to set some quotas to very large/unlimited values to avoid
   running out of quota when deploying multiple or large environments::

    neutron quota-update --security_group 1000
    neutron quota-update --port -1
    neutron quota-update --network -1
    neutron quota-update --subnet -1
    nova quota-update --instances -1 --cores -1 --ram -1 [tenant uuid]

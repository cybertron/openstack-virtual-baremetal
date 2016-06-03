Troubleshooting
===============

This document is intended to be a repository of things that can go wrong in an
OVB deployment, why they go wrong, and how to fix them.

----

*Problem*: Nodes hang while downloading the deploy ramdisk or kernel.

*Cause*: Improper MTU settings on deployment interfaces.

*Solution*: Set the MTU on the deployment interfaces to allow PXE booting to
work correctly.  For TripleO-based deployments, see the readme
for details on how to do this.  For others, make sure that the
deployment nic on the undercloud vm has the MTU set appropriately
and that the DHCP server responding to PXE requests advertises the
same MTU.  Note that this MTU should be 50 bytes smaller than the
physical MTU of the host cloud.

----

*Problem*: Nodes are deployed, but cannot talk to each other.  In OpenStack
deployments, this often presents as rabbitmq connectivity issues
from compute nodes.

*Cause*: Improper MTU settings on deployed instances.

*Solution*: Essentially the same as the previous problem.  Ensure that the MTU
being used on the deployed instances is 50 bytes smaller than the
physical MTU of the host cloud.  Again, for TripleO-based
deployments the readme has details on how to do this.

----

*Problem*: After deploying to an OVB environment once, the nodes refuse to PXE
boot on subsequent deployments.

*Cause*: The nodes are not configured to PXE boot properly.

*Solution*: This depends on the method being used to PXE boot.  If the Nova
patch is being used to provide this functionality, then ensure
that it has been applied on all compute nodes and those nodes'
nova-compute service has been restarted.  If the ipxe-boot image
is being used without the Nova patch, the baremetal instances must
be rebuilt to the ipxe-boot image before subsequent deployments.

----

*Problem*: Nodes fail to PXE boot.  DHCP requests are seen on the undercloud
VM, but responses never get to the baremetal instances.

*Cause*: Neutron port security blocking DHCP from the undercloud.

*Solution*: Neutron either needs to be configured to use the Noop firewall
driver, or the port-security extension must be used to disable
port-security on the appropriate ports.  As of this writing that
requires use of the port-security branch of OVB.

----

*Problem*: The BMC does not respond to IPMI requests.

*Cause*: Several.  Neutron may not be configured to allow the BMC to listen
on arbitrary addresses.  The BMC deployment may have failed for some
reason.

*Solution*: Neutron must be configured to allow the BMC to listen on
arbitrary addresses.  This requires use of the Noop firewall driver
or port-security extension as in the previous solution.  If this
is already configured correctly, then the BMC may have failed to
deploy properly.  This can usually be determined by looking at the
nova console-log of the BMC instance.  A correctly working BMC will
display 'Managing instance [uuid]' for each baremetal node in the
environment.  If those messages are not found, then the BMC has
failed to start properly.  The relevant error messages should be
found in the console-log of the BMC.  If that is not sufficient to
troubleshoot the problem, the BMC can be accessed using the
ssh key configured in the OVB environment yaml as the 'centos'
user.

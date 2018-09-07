Introduction
============

OpenStack Virtual Baremetal is a way to use OpenStack instances to do
simulated baremetal deployments.  This project is a collection of tools
and documentation that make it much easier to do so.  It primarily consists
of the following pieces:

- Patches and documentation for setting up a host cloud.
- A deployment CLI that leverages the OpenStack Heat project to deploy the
  VMs, networks, and other resources needed.
- An OpenStack BMC that can be used to control OpenStack instances via IPMI
  commands.
- A tool to collect details from the "baremetal" VMs so they can be added as
  nodes in the OpenStack Ironic baremetal deployment project.

A basic OVB environment is just a BMC VM configured to control a number
of "baremetal" VMs.  This allows them to be treated largely the same
way a real baremetal system with a BMC would.  A number of additional
features can also be enabled to add more to the environment.

OVB was initially conceived as an improved method to deploy environments for
OpenStack TripleO development and testing.  As such, much of the terminology
is specific to TripleO.  However, it should be possible to use it for any
non-TripleO scenarios where a baremetal-style deployment is desired.

Benefits and Drawbacks
----------------------

As noted above, OVB started as part of the OpenStack TripleO project.
Previous methods for deploying virtual environments for TripleO focused on
setting up all the vms for a given environment on a single box.  This had a
number of drawbacks:

- Each developer needed to have their own system.  Sharing was possible, but
  more complex and generally not done.  Multi-tenancy is a basic design
  tenet of OpenStack so this is not a problem when using it to provision the
  VMs.  A large number of developers can make use of a much smaller number of
  physical systems.
- If a deployment called for more VMs than could fit on a single system, it
  was a complex manual process to scale out to multiple systems.  An OVB
  environment is only limited by the number of instances the host cloud can
  support.
- Pre-OVB test environments were generally static because there was not an API
  for dynamic provisioning.  By using the OpenStack API to create all of the
  resources, test environments can be easily tailored to their intended use
  case.

One drawback to OVB at this time is that it does have hard requirements on a
few OpenStack features (Heat, Neutron port-security, private image uploads,
for example) that are not all widely available in public clouds. Fortunately,
as they move to newer and newer versions of OpenStack that situation should
improve.

It should also be noted that without the Nova PXE boot patch, OVB is not
compatible with any workflows that write to the root disk before deployment.
This includes Ironic node cleaning.

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

#. Deploy a QuintupleO stack::

    bin/deploy.py --quintupleo

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

   .. note:: ``build-nodes-json`` also outputs a file named ``bmc_bm_pairs``
             that lists which BMC address corresponds to a given baremetal
             instance.

   .. note:: If ``--id`` was used to deploy the stack, make sure to pass the
             generated ``env-${id}.yaml`` file to build-nodes-json using the
             ``--env`` parameter.  Example::

                bin/build-nodes-json --env env-foo.yaml

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

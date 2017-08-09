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

             Be aware that when --id is used, a new environment file will
             be generated that reflects the new names.  The name of the new
             file will be ``env-${id}.yaml``.  This new file should be passed
             to build-nodes-json instead of the original.

   .. note:: There are a number of

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

Advanced Options
----------------

There are also a number of advanced options that can be enabled for a
QuintupleO deployment.  For each such option there is a sample environment
to be passed to the deploy command.

For example, to deploy using the Neutron port-security extension to allow
DHCP and PXE booting, the following command could be used::

    bin/deploy.py --quintupleo -e env.yaml -e environments/port-security.yaml

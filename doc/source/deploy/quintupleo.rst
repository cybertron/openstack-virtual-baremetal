Deploying with QuintupleO
=========================

QuintupleO is short for OpenStack on OpenStack on OpenStack.  It was the
original name for OVB, and has been repurposed to indicate that this
deployment method is able to deploy a full TripleO development environment
in one command.  It should be useful for non-TripleO users of OVB as well,
however.

#. Copy the example env file and edit it to reflect the host environment:

   .. note:: QuintupleO environments require a few more configuration
             parameters to be set.  It also allows enabling a few more
             features in env.yaml.

   ::

      cp templates/env.yaml.example env.yaml
      vi env.yaml

#. Deploy a QuintupleO stack::

    bin/deploy.py --quintupleo

   .. note:: There is a quintupleo-specific option ``--id`` in deploy.py.
             It appends the value passed in to the name of all resources
             in the stack.  For example, if ``undercloud_name`` is set to
             'undercloud' and ``--id foo`` is passed to deploy.py, the
             resulting undercloud VM will be named 'undercloud-foo'.  This
             can be helpful for differentiating multiple environments in
             the same host cloud.

             Be aware that when --id is used, a new environment file will
             be generated that reflects the new names.  The name of the new
             file will be ``env-${id}.yaml``.  This new file should be passed
             to build-nodes-json instead of the original.

#. Wait for Heat stack to complete:

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

   .. note:: ``build-nodes-json`` also outputs a file named ``bmc_bm_pairs``
             that lists which BMC address corresponds to a given baremetal
             instance.

   .. note:: If ``--id`` was used to deploy the stack, make sure to pass the
             generated ``env-${id}.yaml`` file to build-nodes-json using the
             ``--env`` parameter.  Example::

                bin/build-nodes-json --env env-foo.yaml

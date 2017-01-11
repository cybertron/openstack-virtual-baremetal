Deploying with QuintupleO
=========================

TBD: Explain the meaning of QuintupleO

#. Copy the example env file and edit it to reflect the host environment::

    cp templates/env.yaml.example env.yaml
    vi env.yaml

#. Deploy a QuintupleO stack::

    bin/deploy.py --quintupleo

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

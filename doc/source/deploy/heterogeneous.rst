Deploying Heterogeneous Environments
====================================

It is possible to deploy an OVB environment with multiple "baremetal"
node types.  The :doc:`QuintupleO <quintupleo>` deployment method must be used, so it
would be best to start with a working configuration for that before
moving on to heterogeneous deployments.

Each node type will be identified as a ``role``.  A simple QuintupleO
deployment can be thought of as a single-role deployment.  To deploy
multiple roles, additional environment files describing the extra roles
are required.  These environments are simplified versions of the
standard environment file.  See ``templates/env-role.yaml.example``
for a starting point when writing these role files.

Steps for deploying the environment:

#. Customize the environment files.  Make sure all environments have a ``role``
   key in the ``parameter_defaults`` section.  When building nodes.json, this
   role will be automatically assigned to the node, so it is simplest to use
   one of the default TripleO roles (control, compute, cephstorage, etc.).

#. Deploy with both roles::

    bin/deploy.py --quintupleo --env env-control.yaml --role env-compute.yaml

#. One Heat stack will be created for each role being deployed.  Wait for them
   all to complete before proceeding.

   .. note:: Be aware that the extra role stacks will be connected to networks
             in the primary role stack, so the extra stacks must be deleted
             before the primary one or the neutron subnets will not delete cleanly.

#. Build a nodes.json file that can be imported into Ironic::

    bin/build-nodes-json --env env-control.yaml

   .. note:: Only the primary environment file needs to be passed here.  The
             resources deployed as part of the secondary roles will be named
             such that they appear to be part of the primary environment.

   .. note:: If ``--id`` was used when deploying, remember to pass the generated
             environment file to this command instead of the original.

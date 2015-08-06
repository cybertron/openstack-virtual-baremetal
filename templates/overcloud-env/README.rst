Overcloud Environment Files
===========================

.. note::

    This template applies a patch to Nova that may not be suitable
    for production deployments.  Use at your own risk.

These yaml files enable RDO Manager to deploy a host cloud capable
of booting OpenStack virtual baremetal instances.
To use them, copy the yaml files in this directory to the undercloud
and pass ``ovb.yaml`` as an additional env file in the
overcloud deploy command::

    openstack overcloud deploy --templates -e ovb.yaml
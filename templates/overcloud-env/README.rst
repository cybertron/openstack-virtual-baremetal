Deploying an Overcloud for Virtual Baremetal
============================================

The files in this directory can be used to deploy an overcloud
using TripleO that is suitable for use as a virtual
baremetal host.  The following are instructions on how to do so.

Custom Environment
------------------

.. note::

    This template applies a patch to Nova that may not be suitable
    for production deployments.  Use at your own risk.

Copy the yaml files to the undercloud so they can be referenced by
the overcloud deploy call.  The ``ovb.yaml`` file must be passed
as an additional ``-e`` parameter.  See `Overcloud Deployment`_ for
an example deploy call.

Hieradata Changes
-----------------

Make a copy of the tripleo-heat-templates directory::

    cp -r /usr/share/openstack-tripleo-heat-templates/ custom

Add the necessary hieradata configuration::

    echo "neutron::agents::ml2::ovs::firewall_driver: neutron.agent.firewall.NoopFirewallDriver" >> custom/puppet/hieradata/common.yaml

Overcloud Deployment
--------------------

Pass both the custom environment and templates to the deploy call::

    openstack overcloud deploy --libvirt-type kvm --templates custom -e ovb.yaml

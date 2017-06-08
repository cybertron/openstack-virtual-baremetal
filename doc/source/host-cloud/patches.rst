Patching the Host Cloud
=======================

The changes described in this section apply to compute nodes in the
host cloud.

Apply the Nova pxe boot patch file in the ``patches`` directory to the host
cloud Nova.  ``nova-pxe-boot.patch`` can be used with all releases prior to
Pike, ``nova-pxe-boot-pike.patch`` must be used with Pike and later.

Examples:

TripleO/RDO::

    sudo patch -p1 -d /usr/lib/python2.7/site-packages < patches/nova/nova-pxe-boot.patch

or

::

    sudo patch -p1 -d /usr/lib/python2.7/site-packages < patches/nova/nova-pxe-boot-pike.patch

Devstack:

.. note:: You probably don't want to try to run this with devstack anymore.
          Devstack no longer supports rejoining an existing stack, so if you
          have to reboot your host cloud you will have to rebuild from
          scratch.

.. note:: The patch may not apply cleanly against master Nova
          code.  If/when that happens, the patch will need to
          be applied manually.

::

    cp patches/nova/nova-pxe-boot.patch /opt/stack/nova
    cd /opt/stack/nova
    patch -p1 < nova-pxe-boot.patch

or

::

    cp patches/nova/nova-pxe-boot-pike.patch /opt/stack/nova
    cd /opt/stack/nova
    patch -p1 < nova-pxe-boot-pike.patch

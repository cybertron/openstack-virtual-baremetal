===============
ipxe-boot-image
===============
Builds an image which contains *only* a grub2 based boot configured to run a
custom built ipxe.lkrn image.

While this element depends on centos7, all remnants of the OS are removed apart
from the /boot grub configuration and modules.

Optional parameters:

 * IPXE_GIT_REF a git reference to checkout from the iPXE git repository before
   building the iPXE image. If not specified then current master will be built.

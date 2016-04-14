# git ref to checkout from the iPXE git repository
IPXE_GIT_REF=6366fa7a

ipxe-boot.qcow2:
	ELEMENTS_PATH=./elements IPXE_GIT_REF=$(IPXE_GIT_REF) disk-image-create -x -o ipxe-boot ipxe-boot-image

clean:
	rm -f ipxe-boot.qcow2

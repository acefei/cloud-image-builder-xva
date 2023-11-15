# Cloud Image Builder for XVA
The tool automates the process of creating cloud images and outputs them in the XVA format. The resulting images can be used with popular cloud platforms such as Xen, XenServer, and Citrix Hypervisor.

# Getting Started
Clone the repository to your local machine and run the following command:
```
$ source run_docker
```
Then you can run a docker wrapper `docker_run <stage name> <options>` for multiple stage in Dockerfile. (Hint: press <tab> for stage name auto-completion)

## XVA Builder
```
$ docker_run xva-builder -h
...
usage: img2xva.py [-h] [-c CPUS] [-m MEMORY] [-s SEED] [-v] [-p] image

Build XVA image from qcow2 or raw image

positional arguments:
  image                 Path of cloud image, only support qcow2 and raw image, you can also use the existed cloud image whose link as follows:
                            Ubuntu: https://cloud-images.ubuntu.com/
                            Debian: https://cloud.debian.org/cdimage/cloud/
                            AmaLinux: https://repo.almalinux.org/almalinux/9/cloud/x86_64/images/


options:
  -h, --help            show this help message and exit
  -c CPUS, --cpus CPUS  CPU Number of VM. Default is 2
  -m MEMORY, --memory MEMORY
                        Memory Size (GB) of VM. Default is 4GB
  -s SEED, --seed SEED  User Data File Path
  -v, --verbose         Enable verbose mode for debugging
  -p, --persist         Persist raw image for inspection


$ docker_run xva-builder -c 2 -m 4 -p -s src/xva-builder/cloud-config-templates/user-data https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img
```
Once build successfully, we can put the generated XVA on xenserver host to install the VM.
```
xe vm-import filename=jammy-server-cloudimg-amd64.xva sr-uuid=<storage uuid>
```
Then you can boot up this VM on xencenter and login it with the credential mentioned in user-data file.

## Inspect image
Sometimes, we need to check if the user-data was inserted in image properly, we can add `-p` option when run `xva-builder`, after that there is a `.raw` suffix image generated, then inspect the image as follows:
```
$ docker_run guestfish --ro -a jammy-server-cloudimg-amd64.raw
...
Welcome to guestfish, the guest filesystem shell for
editing virtual machine filesystems and disk images.

Type: ‘help’ for help on commands
      ‘man’ to read the manual
      ‘quit’ to quit the shell

><fs> run
><fs> list-filesystems
/dev/sda1: ext4
/dev/sda14: unknown
/dev/sda15: vfat
><fs> mount /dev/sda1 /
><fs> ls /
bin
boot
dev
...
><fs>
```

## Validate cloud-init config file

```
$ docker_run cloud-init-validator src/xva-builder/cloud-config-templates/user-data
```

# Guest OS Support
Consistent with the list of Linux Guest in https://docs.citrix.com/en-us/citrix-hypervisor/system-requirements/guest-os-support.html,
And you can obtain cloud image with qcow2 format from the following Linux Guest Vendor.
- Ubuntu: https://cloud-images.ubuntu.com
- Debian: https://cloud.debian.org/cdimage/cloud
- AmaLinux: https://repo.almalinux.org/almalinux


# License
This repository is licensed under the MIT License.

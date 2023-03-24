# Cloud Image Builder XVA
This repository contains a cloud image builder that can create XVA images. The tool automates the process of creating cloud images and outputs them in the XVA format. The resulting images can be used with popular cloud platforms such as Xen, XenServer, and Citrix Hypervisor.

# Getting Started
To use the cloud image builder, follow these steps:

1. Clone the repository to your local machine.
2. Install the necessary dependencies listed in the requirements.txt file.
3. Customize the image by modifying the config.yml file.
4. Run the build.py script to create the image.

# Features
The cloud image builder includes the following features:

[ ] Build XVA image from qcow2 or raw image

[ ] Provide user-data Templates

[ ] Automated build process based on Docker

[ ] Platform support (Xen, XenServer, and Citrix Hypervisor)

# Guest OS Support
Consistent with the list of Linux Guest in https://docs.citrix.com/en-us/citrix-hypervisor/system-requirements/guest-os-support.html,
And you can obtain cloud image with qcow2 format from the following Linux Guest Vendor.
- Ubuntu: https://cloud-images.ubuntu.com/
- Debian: https://cloud.debian.org/cdimage/cloud/
- AmaLinux: https://repo.almalinux.org/almalinux


# License
This repository is licensed under the MIT License.

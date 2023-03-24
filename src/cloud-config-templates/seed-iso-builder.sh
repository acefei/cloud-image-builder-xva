#!/bin/bash

user_data=${1?cloud config is not found in cloud-config-templates dir}
template_path=$(cd "$(dirname "${BASH_SOURCE[0]}")"; pwd -P)
setup=$(mktemp -dt "$(basename "$0").XXXXXXXXXX")
teardown() {
    local exit_code=$?
    if [ $exit_code -eq 0 ];then
        echo "Build Complete Successfully."
        [ -z "$DEBUG_SH" ] || rm -rf $setup
    else
        exit $exit_code
    fi
}
trap teardown EXIT

# Main
cd $setup
echo -e "instance-id: $RANDOM$RANDOM\nlocal-hostname: cloudimg" > meta-data
cloud-init devel schema --config-file user-data
cp $template_path/$user_data .
mkdir -p /output
genisoimage  -output /output/seed.iso -volid cidata -joliet -rock user-data meta-data
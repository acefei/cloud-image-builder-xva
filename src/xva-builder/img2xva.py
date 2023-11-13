#!/usr/bin/python3
# coding=utf-8

import logging
import os
from argparse import ArgumentParser, RawTextHelpFormatter
from errno import ENXIO
from hashlib import sha1
from math import ceil
from pathlib import Path
from string import Template
from subprocess import check_call, check_output
from tempfile import TemporaryDirectory
from time import time,sleep


def copy_and_hash(fin, fout, start, to_copy):
    sha = sha1()
    fin.seek(start)
    buf_size = 1024 * 1024
    while to_copy > 0:
        data = fin.read(min(buf_size, to_copy))
        if not data:
            break  # end of file
        sha.update(data)
        fout.write(data)
        to_copy -= len(data)
    return sha.hexdigest()


def get_next_data_segment(fin, from_pos):
    """
    Uses SEEK_DATA and SEEK_HOLE to discover the sparseness, should be run on a filesystem on which these are efficient.
    """
    try:
        data_start = os.lseek(fin.fileno(), from_pos, os.SEEK_DATA)
    except OSError as error:
        if error.errno == ENXIO:
            # No more data after pos
            return None
        raise
    # This should always succeed because there is a virtual hole at
    # the end of the file
    data_end = os.lseek(fin.fileno(), data_start, os.SEEK_HOLE) - 1
    logging.debug(f"found data: bytes {data_start}-{data_end}")
    return (data_start, data_end)


def get_nonempty_chunks(fin, chunk_size):
    pos = 0
    while True:
        data = get_next_data_segment(fin, pos)
        if not data:
            break
        (data_start, data_end) = data
        chunk_start = int(data_start / chunk_size)
        chunk_end = int(data_end / chunk_size)
        for chunk in range(chunk_start, chunk_end + 1):
            yield chunk
        pos = (chunk_end + 1) * chunk_size


def chunk_img(img, output_dir, chunk_size=1024 * 1024):
    os.makedirs(output_dir, exist_ok=True)
    size = os.path.getsize(img)

    with open(img, "rb") as fin:

        def write_chunk(chunk_no):
            logging.debug(f"{output_dir}: writing chunk {chunk_no}")
            chunk_file = os.path.join(output_dir, "{0:020d}".format(chunk_no))
            with open(chunk_file, "wb+") as out:
                chunk_start = chunk_no * chunk_size
                file_hash = copy_and_hash(fin, out, chunk_start, chunk_size)
            checksum_file = os.path.join(
                output_dir, "{0:020d}.checksum".format(chunk_no)
            )
            with open(checksum_file, "w+") as out:
                out.write(file_hash)

        # We have to save the first block
        write_chunk(0)
        # And we have to save the last block
        last_chunk = int(ceil(size / chunk_size)) - 1
        if last_chunk > 0:
            write_chunk(last_chunk)

        for chunk in get_nonempty_chunks(fin, chunk_size):
            if chunk > 0 and chunk < last_chunk:
                write_chunk(chunk)

    chunk_list = sorted(os.path.join(output_dir, f) for f in os.listdir(output_dir))
    return (size, chunk_list)


def download_image(img):
    logging.info(f"Downloading image {img}")
    check_call(["wget", "-q", "--show-progress", img])


def convert_image(qcow2, image_name):
    logging.info(f"Convert {qcow2} to {image_name}")
    check_call(["qemu-img", "convert", qcow2, image_name])


def check_file_format(img):
    file_format = check_output(["file", img]).decode()
    if "QCOW2" in file_format or "QEMU QCOW Image (v2)" in file_format:
        return "QCOW2"
    if "DOS/MBR" in file_format:
        return "RAW"
    return file_format


def generate_hash():
    current_time = str(time()).encode('utf-8')
    hash_value = sha1(current_time).hexdigest()
    return hash_value[:5]


def insert_seed(image_file, user_data_path):
    with TemporaryDirectory() as temp_mount:
        mount_seed_path = f"{temp_mount}/var/lib/cloud/seed/nocloud"
        logging.debug(f"Insert seed into {mount_seed_path}")
        check_call(["guestmount", "-a", image_file, "-i", temp_mount])
        Path(mount_seed_path).mkdir(parents=True, exist_ok=True)
        with open(f"{mount_seed_path}/meta-data", mode='w') as f:
            random_str = generate_hash()
            f.write(f"local-hostname: xs-vm-{random_str}")

        check_call(["cp", user_data_path, f"{mount_seed_path}/user-data"])
        check_call(["guestunmount", temp_mount])
        # avoid race condition between guestunmount and qemu-img convert
        sleep(1)


def gen_raw_img(image_path, user_data_path=None):
    file_suffix = Path(image_path).suffix
    if file_suffix not in [".raw", ".img", ".qcow2", "image"]:
        raise Exception(
            f"Invalid image {file_suffix}, only support qcow2 and raw image now."
        )

    file_format = check_file_format(image_path)
    if file_format not in ["QCOW2", "RAW"]:
        raise Exception(
            f"Invalid file format: {file_format}, only support qcow2 and raw image now."
        )

    if user_data_path:
        logging.info(f"Copy {user_data_path} in {image_path}")
        insert_seed(image_path, user_data_path)

    converted_image_path = Path(image_path).with_suffix(".raw")
    if file_format == "QCOW2":
        convert_image(image_path, converted_image_path)

    return converted_image_path


def _produce_parser():
    parser = ArgumentParser(
        formatter_class=RawTextHelpFormatter,
        description="Build XVA image from qcow2 or raw image ",
    )
    parser.add_argument(
        "image",
        help="""Path of cloud image, only support qcow2 and raw image, you can also use the existed cloud image whose link as follows:
    Ubuntu: https://cloud-images.ubuntu.com/
    Debian: https://cloud.debian.org/cdimage/cloud/
    AmaLinux: https://repo.almalinux.org/almalinux/9/cloud/x86_64/images/
    """,
    )
    parser.add_argument(
        "-c", "--cpus", type=int, default=2, help="CPU Number of VM. Default is 2"
    )
    parser.add_argument(
        "-m", "--memory", type=int, default=4, help="Memory Size (GB) of VM. Default is 4GB"
    )
    parser.add_argument(
        "-s", "--seed", help="User Data File Path"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Enable verbose mode for debugging"
    )
    parser.add_argument(
        "-p", "--persist", action="store_true", help="Persist raw image for inspection"
    )
    return parser


def main():
    settings = _produce_parser().parse_args()
    log_level = logging.DEBUG if settings.verbose else logging.INFO
    logging.basicConfig(level=log_level, format=("[%(levelname)s] %(message)s"))


    script_dir = Path(__file__).resolve().parent

    image_path = None
    # user-data configuration for cloud image
    seed_path = None

    # check if image is a path or url
    image = settings.image
    if image[0:4] == "http":
        download_image(image)
        image_basename = Path(image).name
        image_path = Path(image_basename).absolute().as_posix()
    else:
        image_path = Path(image).absolute().as_posix()
    
    if settings.seed:
       seed_path = Path(settings.seed).absolute().as_posix()

    # convert to raw image
    logging.info(f"Convert image from {image_path}")
    raw_path = gen_raw_img(image_path, seed_path)
    xva_path = Path(raw_path).with_suffix(".xva")

    # convert raw img to xva format
    with TemporaryDirectory() as tempdir:
        root_vdi_ref = "Ref:VDI-1-root"
        image_name = raw_path.name
        logging.info(f"Chunking {image_name}...")
        (root_size_bytes, root_chunks) = chunk_img(
            img=raw_path, output_dir=f"{tempdir}/{root_vdi_ref}"
        )

        config = {
            # vm name with random string suffix
            "vm_name_label": f"{image_name[:-4]}-{tempdir[8:]}",
            "vm_name_description": image_name,
            "memory_bytes": settings.memory * 1024 * 1024 * 1024,
            "vcpus": settings.cpus,
            "root_vdi_virtual_size_bytes": root_size_bytes,
            "root_vdi_ref": root_vdi_ref,
        }

        ova_xml_path = f"{tempdir}/ova.xml"
        logging.info(f"Populating {ova_xml_path}...")
        with open(f"{script_dir}/ova.xml.in", "r") as fin, open(
            ova_xml_path, "w"
        ) as fout:
            ova = Template(fin.read())
            fout.write(ova.substitute(config))

        logging.info(f"Creating {xva_path}...")
        check_call(
            ["tar", "zchfP", xva_path, "--transform", f"s~{tempdir}/~~", ova_xml_path]
            + root_chunks
        )

    if not settings.persist:
        check_call(["rm", raw_path])


if __name__ == "__main__":
    main()

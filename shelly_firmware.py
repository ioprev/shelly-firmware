#!/usr/bin/env python3

import io
import pysh
import os
import re
import json
import tempfile
import hashlib
import zipfile
import argparse
import requests
import logging

VERSION = '0.1'
cloud_url = 'http://api.shelly.cloud/files/firmware'
flash_size = 2097152

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

tool_mkspiffs = lambda a: pysh.sh(f"./tools/mkspiffs8 {a}", capture=True)
tool_unspiffs = lambda a: pysh.sh(f"./tools/unspiffs8 {a}", capture=True)


def list_dev_from_cloud():
    try:
        logger.debug("Fetching data from URL: {}".format(cloud_url))
        cloud_resp = requests.get(cloud_url)
    except Exception as err:
        logger.exception('An error occurred while fetching device list:' % err)
    logger.debug('Got response {} for URL: {}'.format(cloud_resp.status_code, cloud_url))
    cloud_json = cloud_resp.json()
    if 'isok' in cloud_json and cloud_json['isok']:
        logger.debug('Data JSON received and it looks sane. isok = True')
        return cloud_json['data']


def print_devices(data, beta):
    print('#'*56)
    print("The following devices were found in Shelly cloud\n")
    print("{0:<16}{1:<40}".format("Model", "Release"))
    print('='*56)
    for model, info in data.items():
        try:
            if beta: print("{0:<16}{1:<40}".format(model, info["beta_ver"]))
            else: print("{0:<16}{1:<40}".format(model, info["version"]))
        except KeyError:
            logger.debug("No firmware verion available for model {}".format(model))
    print('#' * 56)


def get_firmware_url(data, model):
    try:
        dev_info = data[model]
    except KeyError:
        logger.exception("Model {} not found in Shelly cloud".format(model))
    logger.debug("Model {} found!".format(model))
    return dev_info["url"]

def build_firmware(input_data, output_file):
    fw_zip = zipfile.ZipFile(io.BytesIO(input_data))
    manifest = fw_get_manifest(fw_zip)
    try:
        platform_name = manifest['name']
    except KeyError:
        logger.exception("Platform name not found in firmware package")
    logger.info("Found platform {} in firmware package".format(platform_name))
    part_list = []
    logger.debug('Iterating over firmware parts...')
    for key, part in manifest['parts'].items():
        start_addr = part["addr"]
        part_size = part["size"]
        if not any([x in part.keys() for x in ("fill","src")]):
            logger.error('Data missing for part {}.'.format(key))
            exit(1)
        if "fill" in part:
            part_data = bytearray([part["fill"]] * part_size)
        if "src" in part:
            part_data = fw_get_part(fw_zip, part["src"])
        if "cs_sha1" in part:
            if not fw_verify_part(part_data, part["cs_sha1"]):
                logger.error("Verification failed. Invalid data for part {}".format(key))
                exit(1)
        logger.debug('Found part {}:\n'.format(key) +
                     '\tStart address: {}\n'.format(hex(int(start_addr))) +
                     '\tSize: {}\n'.format(hex(int(part_size))) +
                     '\tData: {}...'.format(''.join(format(x, '02x') for x in part_data[:32])))
        if 'fs' in key:
            logger.debug('Found SPIFFS data partition of size: {}'.format(part_size))
            part_data = fs_inject_hwinfo(part_data, platform_name)
            part_size = len(part_data)
            logger.debug('New SPIFFS data partition size: {}'.format(part_size))

        part_list.append({
            'start': start_addr,
            'size': part_size,
            'data': part_data
        })
    empty_image = create_flash_image(flash_size)
    flash_image = io.BytesIO(empty_image)
    for part in part_list:
        logger.debug('Writing {} bytes at address {}...'.format(part['size'],
                                                                hex(int(part['start']))))
        flash_image.seek(part['start'])
        flash_image.write(part['data'])
    with open(output_file, "wb") as outfile:
        logger.info('Writing file {}'.format(output_file))
        outfile.write(flash_image.getbuffer())

def download_and_build_firmware(url, output_file):
    try:
        fw_pkg = requests.get(url)
    except Exception as err:
        logger.exception("An error occurred while fetching firmware:" % err)
    build_firmware(fw_pkg.content, output_file)

def build_firmware_from_file(input_file, output_file):
    try:
        file_contents=open(input_file,"rb").read()
    except Exception as err:
        logger.exception("An error occurred while reading input:" % err)
    build_firmware(file_contents, output_file)

def fs_inject_hwinfo(data, name):
    # This will edit SPIFFS filesystem and inject hwinfo
    temp_dir = tempfile.mkdtemp()
    fs_dir = os.path.join(temp_dir, 'out')
    fs_old = os.path.join(temp_dir, 'old.bin')
    fs_new = os.path.join(temp_dir, 'new.bin')
    os.mkdir(fs_dir)
    logger.debug('Created temporary directory {} for unpacking SPIFFS data'.format(fs_dir))

    with open(fs_old, 'wb') as f:
        f.write(data)
        f.flush()

    # Unpack SPIFFS
    cmd = tool_unspiffs(f"-d {fs_dir} {fs_old}")

    if cmd.returncode:
        logger.error('SPIFFS unpacking failed! Cannot unpack!' +
                     f'\n\tCommand output:\n\t{cmd.stdout}' +
                     f'\n\tError message:\n\t{cmd.stderr}')
        exit(1)
    logger.debug('SPIFFS unpack success!' +
                 f'\n\tCommand output\n\t{cmd.stdout}' +
                 f'\n\t{cmd.stderr}')

    # unspiffs tool prints fs info in stderr during unpack

    # File size
    fs_fs = re.search(r'\(.*fs\s(\d+).*\)', cmd.stderr).group(1)
    # Block size
    fs_bs = re.search(r'\(.*bs\s(\d+).*\)', cmd.stderr).group(1)
    # Page size
    fs_ps = re.search(r'\(.*ps\s(\d+).*\)', cmd.stderr).group(1)
    # Erase size
    fs_es = re.search(r'\(.*es\s(\d+).*\)', cmd.stderr).group(1)

    hwinfo = mk_hwinfo_for_platform(name)
    logger.debug('Created hwinfo struct:' +
                 '\n\t{}'.format(hwinfo))
    with open(os.path.join(fs_dir, 'hwinfo_struct.json'), 'w') as f:
        f.write(hwinfo)
        f.flush()

    # Repack SPIFFS
    cmd = tool_mkspiffs(
        f"-s {fs_fs} -b {fs_bs} -p {fs_ps} -e {fs_es} -f {fs_new} {fs_dir}")

    if cmd.returncode:
        logger.error('SPIFFS repacking failed! Cannot create SPIFFS!'
                     f'\n\tCommand output:\n\t{cmd.stdout}' +
                     f'\n\tError message:\n\t{cmd.stderr}')
        exit(1)
    logger.debug('SPIFFS repack success!' +
                 '\n\tCommand output\n\t{}'.format(cmd.stdout.decode(sys.stdout.encoding)) +
                 '\n\t{}'.format(cmd.stderr.decode(sys.stderr.encoding)))

    with open(fs_new, 'rb') as f:
        new_data = bytearray(f.read())

    return new_data


def mk_hwinfo_for_platform(name):
    hwinfo = {
     "selftest": True,
     "hwinfo_ver": 1,
     "batch_id": 1,
     "model": name,
     "hw_revision": "prod-unknown",
     "manufacturer": "device_recovery"
    }
    return json.dumps(hwinfo)


def fw_get_manifest(fw_zip):
    firmware_files = fw_zip.namelist()
    logger.debug('The following files were found in downloaded firmware package'
                 '\n\t{}'.format('\n\t'.join(firmware_files)))
    manifest_name = next(file for file in firmware_files if "manifest" in file)
    logger.debug('The manifest seems to be named {}'.format(manifest_name))
    if not manifest_name:
        logger.error("Manifest file was not found in firmware package!")
        exit(1)
    manifest_file = fw_zip.read(manifest_name)
    try:
        manifest = json.loads(manifest_file)
    except json.JSONDecodeError:
        logger.exception("Cannot decode JSON. Bad manifest format!")
    return manifest


def fw_get_part(fw_zip, part):
    logger.debug('Searching for part {} in firmware package'.format(part))
    firmware_files = fw_zip.namelist()
    logger.debug('The following files were found in downloaded firmware package'
                 '\n\t{}'.format('\n\t'.join(firmware_files)))
    part_name = next(file for file in firmware_files if part in file)
    logger.debug('The file for part {} seems to be named {}'.format(part, part_name))
    if part_name:
        part_data = bytearray(fw_zip.read(part_name))
    else:
        logger.error("Error occurred trying to read data for part {}".format(part))
        exit(1)
    return part_data


def fw_verify_part(data, chksum):
    logger.debug('Part data verification requested')
    algo = hashlib.sha1()
    algo.update(data)
    digest = algo.hexdigest()
    logger.debug('The following checksums were calculated:\n' +
                 '\tData\t\t{}\n'.format(digest) +
                 '\tManifest\t{}'.format(chksum))
    if chksum == digest:
        logger.debug('Checksums match. Success!')
        return True
    return False


def create_flash_image(size):
    logger.debug('Generating empty flash image of {} bytes'.format(size))
    return bytearray([255] * size)


def main():
    # Select action based on arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list", action="store_true",
                        help="List available devices from shelly.cloud")
    parser.add_argument("-b", "--beta", action="store_true",
                        help="List beta versions from shelly.cloud")
    parser.add_argument("-d", "--download", dest="model",
                        help="Download binary for specified device")
    parser.add_argument("-i", "--input", dest="input_file",
                        help="Use the provided .zip file as input, instead of downloading.")
    parser.add_argument("-o", "--output", default="firmware.bin",
                        help="Output file name")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Enable debug output to console")
    args = parser.parse_args()

    # Logging config
    console_handler = logging.StreamHandler()
    if args.verbose:
        console_handler.setLevel(logging.DEBUG)
    else:
        console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('%(levelname)s:\t%(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    file_handler = logging.FileHandler('shelly_firmware.log')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter('%(asctime)s\t[%(levelname)s]: %(message)s')
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    logger.info('Shelly firmware binary download tool. Version {}'.format(VERSION))
    if args.list:
        logger.info('Getting list of available firmware packages from shelly.cloud')
        dev_list = list_dev_from_cloud()
        print_devices(dev_list, args.beta)
        exit(0)
    if args.model:
        logger.info('Downloading firmware binary file for device {}'.format(args.model))
        logger.info('Output file is set to: {}'.format(args.output))
        dev_list = list_dev_from_cloud()
        firmware_url = get_firmware_url(dev_list, args.model)
        download_and_build_firmware(firmware_url, args.output)
        exit(0)
    if args.input_file:
        build_firmware_from_file(args.input_file, args.output)
        exit(0)
    parser.print_help()


if __name__ == "__main__":
    main()

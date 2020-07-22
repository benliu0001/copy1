#!/usr/bin/env python
"""
Bootloader Build Tool

This tool is responsible for building the bootloader from source and copying
the build outputs into the host tools directory for programming.
"""
import argparse
import os
import pathlib
import shutil
import subprocess
import random
import string

FILE_DIR = pathlib.Path(__file__).parent.absolute()

fp = open('secret_build_output.txt', "wb") #make secret_build_output.txt file, w means create if doesn't exist already

key1 = binascii.b2a_hex(os.urandom(32)) #creates a random key by generating a hex of 32 digits
fp.write(key1)  #write the key to the file

fp.close() #close fp (secret_build_output.txt file)


def copy_initial_firmware(binary_path):
    """
    Copy the initial firmware binary to the bootloader build directory
    Return:
        None
    """
    # Change into directory containing tools
    os.chdir(FILE_DIR)
    bootloader = FILE_DIR / '..' / 'bootloader'
    shutil.copy(binary_path, bootloader / 'src' / 'firmware.bin')


def make_bootloader():
    """
    Build the bootloader from source.

    Return:
        True if successful, False otherwise.
    """
    # Change into directory containing bootloader.
    bootloader = FILE_DIR / '..' / 'bootloader'
    os.chdir(bootloader)

    subprocess.call('make clean', shell=True)
    status = subprocess.call('make')

    # Return True if make returned 0, otherwise return False.
    return (status == 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bootloader Build Tool')
    parser.add_argument("--initial-firmware", help="Path to the the firmware binary.", default=None)
    args = parser.parse_args()
    if args.initial_firmware is None:
        binary_path = FILE_DIR / '..' / 'firmware' / 'firmware' / 'gcc' / 'main.bin'
    else:
        binary_path = os.path.abspath(pathlib.Path(args.initial_firmware))

    if not os.path.isfile(binary_path):
        raise FileNotFoundError(
            "ERROR: {} does not exist or is not a file. You may have to call \"make\" in the firmware directory.".format(
                binary_path))

    copy_initial_firmware(binary_path)
    make_bootloader()

fp = open("secret_build_output.txt", "w") #make secret_build_output.txt file, w means create if doesn't exist already

key2 = ''.join(random.choices(string.ascii_letters + string.digits, k=16)) #creates a random key of letters and numbers, 16 characters (16 bytes)


fp.write(key2)  #write the key to the file

fp.close() #close fp (secret_build_output.txt file)






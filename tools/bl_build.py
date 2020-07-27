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
import Crypto.Random
import struct
FILE_DIR = pathlib.Path(__file__).parent.absolute()

fp = open("secret_build_output.txt", "wb").close() # Create Clean file

fp = open("secret_build_output.txt", "ab") # Append data 
# Creates seed
seed = Crypto.Random.get_random_bytes(16)
# Creates numbers for stream cipher
A = Crypto.Random.get_random_bytes(2)
B = Crypto.Random.get_random_bytes(2)
C = Crypto.Random.get_random_bytes(2)
D = Crypto.Random.get_random_bytes(2)
E = Crypto.Random.get_random_bytes(2)
# Writes to file
fp.write(seed)
fp.write(A)
fp.write(B)
fp.write(C)
fp.write(D)
fp.write(E)
fp.close() #close fp (secret_build_output.txt file)


def to_c_array(binary_string):# Converts string for make file
    return "{" + ",".join([hex(c) for c in binary_string]) + "}"
def to_c_long(short):# Converts number to short
    number = struct.unpack('H', short)[0]
    return "{" + f"{number}" + "}"
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
    status = subprocess.call(f'make SEED={to_c_array(seed)} AB={to_c_long(A)} BB={to_c_long(B)} CB={to_c_long(C)} DB={to_c_long(D)} EB={to_c_long(E)}', shell=True) # Send numbers to bootloader
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







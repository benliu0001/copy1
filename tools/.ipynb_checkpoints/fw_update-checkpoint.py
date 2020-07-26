#!/usr/bin/env python
"""
Firmware Updater Tool

A frame consists of two sections:
1. Two bytes for the length of the data section
2. A data section of length defined in the length section

[ 0x02 ]  [ variable ]
--------------------
| Length | Data... |
--------------------

In our case, the data is from one line of the Intel Hex formated .hex file

We write a frame to the bootloader, then wait for it to respond with an
OK message so we can write the next frame. The OK message in this case is
just a zero
"""

import argparse
import struct
import time

from serial import Serial

RESP_OK = b'\x00'
FRAME_SIZE = 16

#when implimenting the HMAC - add hmac as another argument
def send_metadata(ser, metadata, debug=False):
    version, size, HMAC = struct.unpack_from('<HH32s', metadata)
    print(f'**UPDATE TOOL** Version: {version}\nSize: {size} bytes\nHMAC: {HMAC}\n')


    # Handshake for update
    ser.write(b'U')
    
    print('Waiting for bootloader to enter update mode...')
    while ser.read(1).decode() != 'U':
        pass

    # Send size and version to bootloader.
    if debug:
        print("**UPDATE TOOL/metadata**",metadata)

    ser.write(metadata)
    print("update tool - attempted to send metadata")
    #ser.write(hmac) #writes the hmac. We need to change the function to be able to pass in an 'hmac' parameter
    # Wait for an OK from the bootloader.
    resp = ser.read()
    print("update tool - this is the responce, want 00s??",resp)
    if resp != RESP_OK:
        raise RuntimeError("ERROR: Bootloader responded with {}".format(repr(resp)))


def send_frame(ser, frame, debug=False):
    ser.write(frame)  # Write the frame...

    if debug:
        print("**UPDATE TOOL/frame**",frame)

    resp = ser.read()  # Wait for an OK from the bootloader

    time.sleep(0.1)

    if resp != RESP_OK:
        raise RuntimeError("ERROR: Bootloader responded with {}".format(repr(resp)))

    if debug:
        print("**UPDATE TOOL** Resp: {}".format(ord(resp)))


def main(ser, infile, debug):
    # Open serial port. Set baudrate to 115200. Set timeout to 2 seconds.
    with open(infile, 'rb') as fp:
        firmware_blob = fp.read()


    metadata = firmware_blob[:68]
    #figure out how long hmac is
    #hmac = firmware_blob[4:36]
    firmware = firmware_blob[68:] #new line after HMAC is implemented: firmware = firmware_blob[36:]
    print("**UPDATE TOOL, metadata in main func",metadata)
    
    send_metadata(ser, metadata, debug=debug)
    for idx, frame_start in enumerate(range(0, len(firmware), 1058)):
        data = firmware[frame_start: frame_start + 1058]
        # Get length of data.
     #   length = len(data)
      #  frame_fmt = '>H{}s'.format(length)

        # Construct frame.
   #     frame = struct.pack(frame_fmt, length, data)
        if debug:
            print("UPDATE TOOL - Writing frame {} ({} bytes)...".format(idx, len(data)))
            
        send_frame(ser, data, debug=debug)
        
    print("UPDATE TOOL - Done writing firmware.")

    # Send a zero length payload to tell the bootlader to finish writing it's page.
    ser.write(struct.pack('>H', 0x0000))

    return ser


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Firmware Update Tool')

    parser.add_argument("--port", help="Serial port to send update over.",
                        required=True)
    parser.add_argument("--firmware", help="Path to firmware image to load.",
                        required=True)
    parser.add_argument("--debug", help="Enable debugging messages.",
                        action='store_true')
    args = parser.parse_args()

    print('Opening serial port...')
    ser = Serial(args.port, baudrate=115200, timeout=2)
    main(ser=ser, infile=args.firmware, debug=args.debug)



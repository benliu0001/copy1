"""
Firmware Bundle-and-Protect Tool

"""

import argparse
import struct
from Crypto.Cipher import AES

def protect_firmware(infile, outfile, version, message):
    #128 bytes per 'frame'
    
    # Load firmware binary from infile
    with open(infile, 'rb') as fp:
        firmware = fp.read()
    firmware_and_message = firmware + message.encode() + b'\00'
    lengthfirm = len(firmware) 
    metadata = struct.pack('<HH', version, lengthfirm)
    framenum = 1
    #Load key from secret_build_output.txt
    with open(secret_build_output.txt, 'rb') as sbo:
        key = sbo.read()
        #if we were to have a seed, would happen here??

    #write metadata to outfile
    with open(outfile, 'wb+') as outfile:
        outfile.write(metadata)
        
    # split into 128 bytes and encrypting it 
    for i in range(0,len(firmware_and_message),1024):
        #double check the <h1024s??
        frame = struct.pack('<h1024s',framenum,firmware_and_message[i:i+1024])
        framenum+=1
        frame_encrypt = AES.new(key, AES.MODE_GCM)
        frame_encrypt.update(metadata)
        ciphertext, tag = frame_encrypt.encrypt_and_digest(frame)
        nonce = frame_encrypt.nonce
        

        #nonce | length ciphertext | length tag | ciphertext (within has framenum then firmware/release message) | tag
        sendoverframe = struct.pack('<16s{0}shh{1}s{2}s'.format(len(ciphertext), len(tag)),len(nonce), nonce, len(ciphertext), len(tag), ciphertext, tag)


        # Write the encrypted frame to outfile
        with open(outfile, 'wb+') as outfile:
            outfile.write(sendoverframe)
    
    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Firmware Update Tool')
    parser.add_argument("--infile", help="Path to the firmware image to protect.", required=True)
    parser.add_argument("--outfile", help="Filename for the output firmware.", required=True)
    parser.add_argument("--version", help="Version number of this firmware.", required=True)
    parser.add_argument("--message", help="Release message for this firmware.", required=True)
    args = parser.parse_args()

    protect_firmware(infile=args.infile, outfile=args.outfile, version=int(args.version), message=args.message)

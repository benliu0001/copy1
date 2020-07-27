"""
Firmware Bundle-and-Protect Tool
"""

import argparse
import struct
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256
import os
from Crypto.Util.Padding import pad, unpad
import random

def get_HMAC(data, key1):
    secret = key1
    h = HMAC.new(secret, digestmod=SHA256)
    h.update(data)
    return h.digest()

    #make sure it works on the bootloader side


#Stream cipher for key gen
def KSA(key): #creates an array with values 0-255 in random order (based on key)
    key_length = len(key)
    S = []# [0,1,2, ... , 255]
    for n in range(256):
        S.append(n)
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % key_length]) % 256
        temp = S[i] #swap S[i] and S[j]
        S[i] = S[j]
        S[j] = temp
    return S


def PRGA(S): #Pseudo-random generation algorithm - creates a generator object (K)
    i = 0
    j = 0
    while True:
        i = (i + 1) % 256
        j = (j + S[i]) % 256
        # swap values
        temp = S[i] 
        S[i] = S[j]
        S[j] = temp
        K = S[(S[i] + S[j]) % 256]
        yield K


def get_key(key, startval): #getting the actual key to use, startval is any value - needs to be sent to bootloader independently
    
    gen=PRGA(KSA(key)) # generator
    streamkey = []
    for j in range(startval):
        next(gen)
    for i in range(16):
        streamkey.append(next(gen))
    return bytes(streamkey)

def protect_firmware(infile, outfile, version, message): #Big Function - encypts
    #1 page per 'frame'
    #Load key from secret_build_output.txt
    with open('secret_build_output.txt', 'rb') as sbo:
        seed = sbo.read(16)
        a = struct.unpack('H', sbo.read(2))[0]
        print(a)
        b = struct.unpack('H', sbo.read(2))[0]
        c = struct.unpack('H', sbo.read(2))[0]
        d = struct.unpack('H', sbo.read(2))[0]
        e = struct.unpack('H', sbo.read(2))[0]
#         aeskey = sbo.read(16)    - - this is for no stream cipher
#         firmkey = sbo.read(16)
#         metakey = sbo.read(16)
        #if we were to have a seed, would happen here??
    
    # Load firmware binary from infile
    with open(infile, 'rb') as fp:
        firmware = fp.read()
    firmware_and_message = firmware + message.encode() + b'\x00'
    lengthfirm = len(firmware) 
    
    #getting all the keys
    aeskey = get_key(seed, (version*lengthfirm*a)%b)
    firmkey = get_key(seed, (lengthfirm*lengthfirm)%c)
    metakey = get_key(seed, (version*d)%(lengthfirm%e))
    
    hmac = get_HMAC(firmware, firmkey)
    metahmac = get_HMAC(struct.pack('<HH', version, lengthfirm), metakey)
    metadata = struct.pack('<HH32s32s', version, lengthfirm, hmac, metahmac)
    

    #write metadata to outfile
    with open(outfile, 'wb') as f:
        f.write(metadata)
        # do we write the HMAC here as well?
    

    # split into 1024 bytes and encrypting it 
    for i in range(0,len(firmware_and_message),1024):

        dataBeforeEncrypt = firmware_and_message[i:i+1024]
        frame = struct.pack('{}s'.format(len(dataBeforeEncrypt)), dataBeforeEncrypt)
        frame_encrypt = AES.new(aeskey, AES.MODE_GCM)
        frame_encrypt.update(metadata[0:4])
        ciphertext, tag = frame_encrypt.encrypt_and_digest(frame)
        nonce = frame_encrypt.nonce
        #nonce | length ciphertext | ciphertext (within has framenum then firmware/release message) | tag
        sendoverframe = struct.pack('<16sH{}s16s'.format(len(ciphertext)), nonce, len(dataBeforeEncrypt), ciphertext, tag)

        # Write the encrypted frame to outfile
        with open(outfile, 'ab') as fb:
            fb.write(sendoverframe)
            


    


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Firmware Update Tool')
    parser.add_argument("--infile", help="Path to the firmware image to protect.", required=True)
    parser.add_argument("--outfile", help="Filename for the output firmware.", required=True)
    parser.add_argument("--version", help="Version number of this firmware.", required=True)
    parser.add_argument("--message", help="Release message for this firmware.", required=True)
    args = parser.parse_args()

<<<<<<< HEAD
    protect_firmware(infile=args.infile, outfile=args.outfile, version=int(args.version), message=args.message)
=======
    protect_firmware(infile=args.infile, outfile=args.outfile, version=int(args.version), message=args.message)
>>>>>>> 466441fb733f9a45d8d927b23765d40675d7544e

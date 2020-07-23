"""
Firmware Bundle-and-Protect Tool

"""

import argparse
import struct
from Crypto.Cipher import AES
from Crypto.Hash import HMAC, SHA256
import os
from Crypto.Util.Padding import pad, unpad

#def get_HMAC(data, key): #returns an hmac in the bytearray format based on the data you want to hash. (data) parameter represents the data to be hashed, (key) represents the key to do the HMAC off of
#   secret = key
#   h = HMAC.new(secret, digestmod=SHA256)
#   h.update(data)
#   return h.digest()
#   #make sure it works on the bootloader side

def protect_firmware(infile, outfile, version, message):
    #1 page per 'frame'
    
    # Load firmware binary from infile
    with open(infile, 'rb') as fp:
        firmware = fp.read()
    firmware_and_message = firmware + message.encode() + b'\x00'
    lengthfirm = len(firmware_and_message) 
    metadata = struct.pack('<HH', version, lengthfirm)
    #we gotta make an HMAC_Key
    #HMAC_Key = 'iudffgeuijheraiujkhagrehjnikrgenjk' # (needs to be a byearray, and we need to make a separate HMAC key)!!!!! 
    #hmac = get_HMAC(metadata, HMAC_key)
    
    #Load key from secret_build_output.txt
   # with open('secret_build_output.txt', 'rb') as sbo:
        #key = sbo.read()
        #if we were to have a seed, would happen here??

    #write metadata to outfile

    with open(outfile, 'wb') as f:
        f.write(metadata)
        # do we write the HMAC here as well?
        

    # split into 1024 bytes and encrypting it 
    for i in range(0,len(firmware_and_message),1024):
        #double check the <h1024s??
        whatwewant = firmware_and_message[i:i+1024]
        frame = struct.pack('{}s'.format(len(whatwewant)), whatwewant)
        frame_encrypt = AES.new("This is a keyhhh".encode(), AES.MODE_GCM)
        frame_encrypt.update(metadata)
        ciphertext, tag = frame_encrypt.encrypt_and_digest(frame)
        nonce = frame_encrypt.nonce
        #nonce | length ciphertext | ciphertext (within has framenum then firmware/release message) | tag
        sendoverframe = struct.pack('<16sH{}s16s'.format(len(ciphertext)), nonce, len(whatwewant), ciphertext, tag)

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

    protect_firmware(infile=args.infile, outfile=args.outfile, version=int(args.version), message=args.message)


# '''
# #stream cipher: KSA() is function for making key - K
# #               PRGA() is function for making initial vector - S

# MOD = 256

# def KSA(key):
# '''
# ''' Key Scheduling Algorithm (from wikipedia):
#     for i from 0 to 255
#         S[i] := i
#     endfor
#     j := 0
#     for i from 0 to 255
#         j := (j + S[i] + key[i mod keylength]) mod 256
#         swap values of S[i] and S[j]
#     endfor
# '''
# '''
#   key_length = len(key)
#   # create the array "S"
#   S = range(MOD)  # [0,1,2, ... , 255]
#   j = 0
#   for i in range(MOD):
#     j = (j + S[i] + key[i % key_length]) % MOD
#     S[i], S[j] = S[j], S[i]  # swap values

#   return S


# def PRGA(S):
# '''
# ''' Psudo Random Generation Algorithm (from wikipedia):
#     i := 0
#     j := 0
#     while GeneratingOutput:
#         i := (i + 1) mod 256
#         j := (j + S[i]) mod 256
#         swap values of S[i] and S[j]
#         K := S[(S[i] + S[j]) mod 256]
#         output K
#     endwhile
# '''
# '''
#   i = 0
#   j = 0
#   while True:
#     i = (i + 1) % MOD
#     j = (j + S[i]) % MOD

#     S[i], S[j] = S[j], S[i]  # swap values
#     K = S[(S[i] + S[j]) % MOD]
#     yield K


# def get_keystream(key):
#     '''
#     ''' Takes the encryption key to get the keystream using PRGA
#         return object is a generator
#     '''
#     '''
#   S = KSA(key)
#   return PRGA(S)


# #function to encrypt plaintext (eventually firmware?) with key from secret...txt file: encrypy()
# #func to decrypt: decryption using key from secret_build_output.txt file and ciphertext:

# def encrypt(keystream, plaintext):    
#   res = []
#   for c in plaintext:
#     val = ("%02X" % (ord(c) ^ next(keystream)))  # XOR and taking hex
#     res.append(val)
#   return ''.join(res)


# def decrypt(keystream, ciphertext):
#     #keystream -> encryption key used for encrypting, as hex string
#      #ciphertext -> hex encoded ciphered text using RC4
    
#   ciphertext = ciphertext.decode('hex')
#  # print('ciphertext to func:', ciphertext)
#   res = encrypt(keystream, ciphertext)
#   return res.decode('hex')


# #generate a keystream
# with open('secret_build_output.txt') as fp:
#   key1 = f.readline() #key is encryption key used for encrypting, as hex string

# key2 = key1.decode('hex')
# key2 = [ord(c) for c in key]

# keystream = get_keystream(key2) #keystream is now generated


# # encrypt the plaintext, using key and RC4 algorithm
# plaintext = 'this is the plaintext'  # plaintext is what we will encrypt, replace it with firmware?
# ciphertext = encrypt(keystream, plaintext)
# #print('plaintext:', plaintext)
# #print('ciphertext:', ciphertext)


# #decrypt the firmware (will need this in later tool I think)
# decrypted = decrypt(keystream, ciphertext)
# #print('decrypted:', decrypted)



# '''
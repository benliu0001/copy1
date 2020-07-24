# design-challenge-error-404-brain-not-found
design-challenge-error-404-brain-not-found created by GitHub Classroom

This is a readme file. Read me!

We need to do more in-depth stuff

jakes advice: I would give an overview of the protocol used in your design, and any details you want on the bootloader code, such as when/how data is written to flash, how you do version checking, etc. You can put more detail/explanation of how things work in your source code with comments and good variable names. And if there's any diagrams you think don't make sense to put in the readme (or are too large), you can make a separate document for them. -give the reader a pretty good understanding of your protocol and how data is encrypted,authenticated, and integrity checked

xqcL

Stream cipher:
  - we use the stream cipher to create a key stream that is pseudorandom, and go to a random index of the keystream, then read the next 16 bytes as a key

bl_build: 
  - Create a seed for the key stream cipher
  - Store this seed with the rest of the code for the bootloader, as well as in the secret_build_output.txt file. 
  - The bootloader generates a main.bin file which has contents of flash memory

fw_protect:
  - Use GCM to encrypt and add a data signature to the Firmware and packages the metadata. 
  - It will use a key generated from the seed stored in the secret_build_output.txt file and a key number to determine which part of the stream cipher to use. 
//- The metadata will include the key number that will eventually specify to the bootloader which evolution of the stream cipher to use as a key. 
  
  - We break the firmware into smaller frames and protect them individually.
    - We are HMAC'ing the entire firmware, and we are HMAC'ing the metadata as well. These two HMACs are packaged together with the metadata.
   

fw_update:
  - Using the data package bundled by the protect tool, communicate with the bootloader to upload the firmware package to the bootloader. 
  - The first 16 bytes of each frame being sent is the IV for each frame
  - Protocol:
    - Handshake (update tool sends U, bootloader sends a U back)
    - Update tool sends over the metadata package (in frames if necessary)
    - Update tool then creates frames (using a piece of the data package and the size of that frame) and sends it to the bootloader sequentially, checking for an ok message each time. 
    - Send a black frame to indicate it is done sending frames

bootloader:
  - we verify and decrypt all our cryptographic primitives in the bootloader
  - Read in the metadata, store it on SRAM 
  - Save incoming firmware on SRAM before loading firmware so you can check the authenticity of the firmware. 
  - Produce the correct key using the key number on the metadata and the stream cipher with the seed key. 
  - Decrypt the data using the correct key.
  - Authenticate the authentication tag and check the version number.
  - If everything checks out, move firmware to the location of the running firmware in FLASH (main.bin)
  - If there is an error, delete firmware, and make the update tool wait 1 second.

# design-challenge-error-404-brain-not-found
design-challenge-error-404-brain-not-found created by GitHub Classroom

This is a readme file. Read me!

We need to do more in-depth stuff

jakes advice: I would give an overview of the protocol used in your design, and any details you want on the bootloader code, such as when/how data is written to flash, how you do version checking, etc. You can put more detail/explanation of how things work in your source code with comments and good variable names. And if there's any diagrams you think don't make sense to put in the readme (or are too large), you can make a separate document for them. -give the reader a pretty good understanding of your protocol and how data is encrypted,authenticated, and integrity checked

xqcL

## bl_build: 
  - Creates a seed for the key stream cipher
  - Stores this seed with the rest of the code for the bootloader, as well as in the secret_build_output.txt file. 
  - The bootloader generates a main.bin file which has contents of flash memory

## fw_protect:
  - Reads in infile, version nuber, and release message
  
  ### Protocol:
    - Combines release message and firmware while adding a nullbyte as a terminator
    - Generates key from stream cipher
    - Creates METADATA(version, size, and HMACS)
    - Creates an HMAC of the firmware and one of the Version and Size using two different keys and adds to METADATA
    - Breaks the firmware into frames with the first 16 bytes being IV, next 2 being size, at most 1kb of cipher text, and the tag as the last 16
    - Writes METADATA and framed firmware with release message to outdata

## fw_update:
  - Sends the data from the infile to the bootloader
  
  ### Protocol:
    - Handshake (update tool sends U, bootloader sends a U back)
    - Update tool sends over the metadata package (in frames if necessary)
    - Waits for "OK" byte before sending next frame
    - Send a black frame to indicate it is done sending frames

## bootloader:
  - Loads or boots firmware
  - Rejects older versions or invalid firmware
  - Generates key with stream cipher
  ### Protocol:
    - Waits for byte to specify mode: "U" for update; "B" for boot
   
   #### Update mode:
      - Reads METADATA from update tool
      - Creates key with stream cipher
      - Verifies METADATA HMAC
      - If correct, writes METADATA to address 0xFC00
      - Reads each frame of firmware
      - Uses provided IV to decrypt data
      - Flashes to storage
      - Verifies firmware HMAC
      - If wrong, erases firmware
      - Sends "OK" to indicate end of update
   #### Boot mode:
      - Prints release message
      - Boots firmware
   

// Hardware Imports
#include "inc/hw_memmap.h" // Peripheral Base Addresses
#include "inc/lm3s6965.h" // Peripheral Bit Masks and Registers
#include "inc/hw_types.h" // Boolean type
#include "inc/hw_ints.h" // Interrupt numbers

// Driver API Imports
#include "driverlib/flash.h" // FLASH API
#include "driverlib/sysctl.h" // System control API (clock/reset)
#include "driverlib/interrupt.h" // Interrupt API

// Application Imports
#include "uart.h"
#include "bearssl.h"
#include <stdio.h> 

// Forward Declarations
void load_initial_firmware(void);
void load_firmware(void);
void boot_firmware(void);
long program_flash(uint32_t, unsigned char*, unsigned int);


// Firmware Constants
#define METADATA_BASE 0xFC00  // base address of version and firmware size in Flash
#define FW_BASE 0x10000  // base address of firmware in Flash


// FLASH Constants
#define FLASH_PAGESIZE 1024
#define FLASH_WRITESIZE 4


// Protocol Constants
#define OK    ((unsigned char)0x00)
#define ERROR ((unsigned char)0x01)
#define UPDATE ((unsigned char)'U')
#define BOOT ((unsigned char)'B')


// Firmware v2 is embedded in bootloader
extern int _binary_firmware_bin_start;
extern int _binary_firmware_bin_size;


// Device metadata
uint16_t *fw_version_address = (uint16_t *) METADATA_BASE;
uint16_t *fw_size_address = (uint16_t *) (METADATA_BASE + 2);
uint8_t *fw_release_message_address;

// Firmware Buffer
unsigned char data[FLASH_PAGESIZE];


int main(void) {

  // Initialize UART channels
  // 0: Reset
  // 1: Host Connection
  // 2: Debug
  uart_init(UART0);
  uart_init(UART1);
  uart_init(UART2);

  // Enable UART0 interrupt
  IntEnable(INT_UART0);
  IntMasterEnable();

  load_initial_firmware();

  uart_write_str(UART2, "Welcome to the BWSI Vehicle Update Service!\n");
  uart_write_str(UART2, "Send \"U\" to update, and \"B\" to run the firmware.\n");
  uart_write_str(UART2, "Writing 0x20 to UART0 will reset the device.\n");

  int resp;
  while (1){
    uint32_t instruction = uart_read(UART1, BLOCKING, &resp);
    if (instruction == UPDATE){
      uart_write_str(UART1, "U");
      load_firmware();
    } else if (instruction == BOOT){
      uart_write_str(UART1, "B");
      boot_firmware();
    }
  }
}


/*
 * Load initial firmware into flash
 */
void load_initial_firmware(void) {

  if (*((uint32_t*)(METADATA_BASE+512)) != 0){
    /*
     * Default Flash startup state in QEMU is all zeros since it is
     * secretly a RAM region for emulation purposes. Only load initial
     * firmware when metadata page is all zeros. Do this by checking
     * 4 bytes at the half-way point, since the metadata page is filled
     * with 0xFF after an erase in this function (program_flash()).
     */
    return;
  }

  int size = (int)&_binary_firmware_bin_size;
  int *data = (int *)&_binary_firmware_bin_start;
    
  uint16_t version = 2;
  uint32_t metadata = (((uint16_t) size & 0xFFFF) << 16) | (version & 0xFFFF);
  program_flash(METADATA_BASE, (uint8_t*)(&metadata), 4);
  fw_release_message_address = (uint8_t *) "This is the initial release message.";
    
  int i = 0;
  for (; i < size / FLASH_PAGESIZE; i++){
       program_flash(FW_BASE + (i * FLASH_PAGESIZE), ((unsigned char *) data) + (i * FLASH_PAGESIZE), FLASH_PAGESIZE);
  }
  program_flash(FW_BASE + (i * FLASH_PAGESIZE), ((unsigned char *) data) + (i * FLASH_PAGESIZE), size % FLASH_PAGESIZE);
}

// secret_build_output.txt
/*
 * Load the firmware into flash.
 */
void load_firmware(void)
{
      int frame_length = 0;
      int read = 0;
      int i;
      uint32_t rcv = 0;
      char tag[16];
      size_t data_length, aad_length;
      aad_length = 4;
      char hmac[32];
      char metamac[32];
      int randomcounter = 0;
      int erasingadd = 0;
      char comparemeta[32];
      char comparehmac[32];
      char iv[16];
      char aeskey[16] = AESKEY;
      char firmkey[16] = FIRMKEY;
      char metakey[16] = METAKEY;
      size_t iv_length, key_length;
      size_t firmware_length;
      iv_length = 16;
      key_length = 16;
      uint32_t data_index = 0;
      uint32_t page_addr = FW_BASE;
      uint32_t version = 0;
      uint32_t size = 0;
      //V 0.7/
      //V 0.8(Deleted frame_number)
      //V 1.1 Removed strings, decryption works, adding hmac for first time
      //V 1.2 added more strings, fixing hmac, hoopefully i cleared the strings
      //V 1.3 Cleared writing to UART2, fixed HMAC, adding additional HMAC fore meta data and hopefully etra keys
      //V 1.4 HMACs work, but when HMAC fails no significant deletion of the firmware happens
      //V 1.4.1 Added extra keys

      // Initiate context structs for GCM
      br_aes_ct_ctr_keys ctrc;
      br_gcm_context gcmc;

      // Initiate context structs for HMAC
      br_hmac_key_context metac;
      br_hmac_key_context firmc;
      br_hmac_context hmetac;
      br_hmac_context hmc;
      
      // Create contexts for HMAC
      br_hmac_key_init(&metac, &br_sha256_vtable, metakey, key_length);
      br_hmac_key_init(&firmc, &br_sha256_vtable, firmkey, key_length);
      br_hmac_init(&hmetac, &metac, 0);
      br_hmac_init(&hmc, &firmc, 0);
    
      // Create contexts for cipher
      br_aes_ct_ctr_init(&ctrc,aeskey,key_length);
      br_gcm_init(&gcmc, &ctrc.vtable, br_ghash_ctmul32);
    

      // Get version.
      rcv = uart_read(UART1, BLOCKING, &read);
      version = (uint32_t)rcv;
      rcv = uart_read(UART1, BLOCKING, &read);
      version |= (uint32_t)rcv << 8;

      uart_write_str(UART2, "Received Firmware Version: ");
      uart_write_hex(UART2, version);
      nl(UART2);

      // Get size.
      rcv = uart_read(UART1, BLOCKING, &read);
      size = (uint32_t)rcv;
      rcv = uart_read(UART1, BLOCKING, &read);
      size |= (uint32_t)rcv << 8;
    
      firmware_length = (size_t) size;

      uart_write_str(UART2, "Received Firmware Size: ");
      uart_write_hex(UART2, size);
      nl(UART2);

         
      //Get HMAC
        for(i = 0; i < 32; i++){
            hmac[i] = uart_read(UART1, BLOCKING, &read);
        }

      //Get HMAC for meta data
        for(i = 0; i < 32; i++){
            metamac[i] = uart_read(UART1, BLOCKING, &read);
        }


      // Compare to old version and abort if older (note special case for version 0).
      uint16_t old_version = *fw_version_address;
    
      // Creates metadata number
      
      int32_t metadata = ((size & 0xFFFF) << 16) | (version & 0xFFFF);
    
      // Compute the HMAC for the meta data
      br_hmac_update(&hmetac, &metadata, 4);
      br_hmac_out(&hmetac, comparemeta);
      for(i = 0; i < 32; i++){
      uart_write(UART2, comparemeta[i]);
  }
      nl(UART2);
      for(i = 0; i < 32; i++){
      uart_write(UART2, metamac[i]);
  }
      //  Compare the HMACs
      for(i = 0; i < 32; i++){
      if(comparemeta[i]!=metamac[i]){
          uart_write_str(UART2, "\nHMAC failed");
          SysCtlReset();
          return;
      }
  }

          
      uart_write_str(UART2, "\nHMAC passed\n");
    
      if (version != 0 && version < old_version) {
        uart_write(UART1, ERROR); // Reject the metadata.
        SysCtlReset(); // Reset device
        return;
      } else if (version == 0) {
        // If debug firmware, don't change version
        version = old_version;
      }

      // Write new firmware size and version to Flash
      // Create 32 bit word for flash programming, version is at lower address, size is at higher address
      program_flash(METADATA_BASE, (uint8_t*)(&metadata), 4);
      fw_release_message_address = (uint8_t *) (FW_BASE + size);
      uart_write(UART1, OK); // Acknowledge the metadata.
      
      /* Loop here until you can get all your characters and stuff */
      while (1) {
          
        //Counts the amount of pages flashed 
        randomcounter++;
          
        // Read the nonce.
        for(i = 0; i < 16; i++){
          iv[i] = uart_read(UART1, BLOCKING, &read);
        }

        // Get two bytes for the length.
        rcv = uart_read(UART1, BLOCKING, &read);
        frame_length = (int)rcv; 
        rcv = uart_read(UART1, BLOCKING, &read);
        frame_length += (int)rcv << 8;

        // Write length debug message
        uart_write_hex(UART2, frame_length);
        nl(UART2);


        // Get the number of bytes specified
        for (i = 0; i < frame_length; ++i){
            data[data_index] = uart_read(UART1, BLOCKING, &read);
            data_index += 1;
        } //for
          
          
        //Read the Auth Tag
        for (i = 0; i < 16; i++){
            tag[i] = uart_read(UART1, BLOCKING, &read);
        }
          
          
      // Reset the GCM context 
      br_gcm_reset(&gcmc, iv, iv_length);
          
      // Decrypt Data
      br_gcm_aad_inject(&gcmc, &metadata ,aad_length);
      br_gcm_flip(&gcmc);
      data_length = (size_t) data_index;
      br_gcm_run(&gcmc, 0, data, data_length);
          
      // Checks for authentication from the tag
      if(!br_gcm_check_tag(&gcmc, tag)) {
      erasingadd = 0x10000;
      uart_write_str(UART2, "Authentication failed");
      for(i = 0; i < randomcounter; i++){
          uart_write_str(UART2, "Deleting page: ");
          uart_write_hex(UART2, i + 1);
          uart_write_str(UART2, "...\n");
          FlashErase(erasingadd);
          erasingadd += FLASH_PAGESIZE;
      }
      SysCtlReset();
      return; 
      }   
      // Try to write flash and check for error
      if (program_flash(page_addr, data, data_index)){
        uart_write(UART1, ERROR); // Reject the firmware
        SysCtlReset(); // Reset device
        return;
      }
      
#if 1
      // Write debugging messages to UART2.
      uart_write_str(UART2, "Page successfully programmed\nAddress: ");
      uart_write_hex(UART2, page_addr);
      uart_write_str(UART2, "\nBytes: ");
      uart_write_hex(UART2, data_index);
      nl(UART2);
#endif

      // Update to next page
      page_addr += FLASH_PAGESIZE;
      data_index = 0;
      
      // Clears the array
      for(i = 0; i < 1024; i++){
          data[i] = 0;
      }
         
      // If at end of firmware, go to main
      if (frame_length < 1024) {
        uart_write(UART1, OK);
        break;
      }
          
    uart_write(UART1, OK); // Acknowledge the frame.
  } // while(1)
  // Compare the HMAC    
  br_hmac_update(&hmc, (char *)FW_BASE, firmware_length);
  br_hmac_out(&hmc, comparehmac);
  for(i = 0; i < 32; i++){
      uart_write(UART2, comparehmac[i]);
  }
    nl(UART2);
  for(i = 0; i < 32; i++){
      uart_write(UART2, hmac[i]);
  }
    nl(UART2);
  for(i = 0; i < 32; i++){
      if(comparehmac[i]!=hmac[i]){
          erasingadd = 0x10000;
          for(i = 0; i < randomcounter; i++){
          uart_write_str(UART2, "Deleting page: ");
          uart_write_hex(UART2, i + 1);
          uart_write_str(UART2, "...\n");
          FlashErase(erasingadd);
          erasingadd += FLASH_PAGESIZE;
      }
          uart_write_str(UART2, "\nHMAC failed\n");
          SysCtlReset();
          return;
      }
  }
     
      uart_write_str(UART2, "\nHMAC passed\n");
      SysCtlReset();
  }
  

/*
 * Program a stream of bytes to the flash.
 * This function takes the starting address of a 1KB page, a pointer to the
 * data to write, and the number of byets to write.
 *
 * This functions performs an erase of the specified flash page before writing
 * the data.
 */
long program_flash(uint32_t page_addr, unsigned char *data, unsigned int data_len)
{
  unsigned int padded_data_len;

  // Erase next FLASH page
  FlashErase(page_addr);

  // Clear potentially unused bytes in last word
  if (data_len % FLASH_WRITESIZE){
    // Get number unused
    int rem = data_len % FLASH_WRITESIZE;
    int i;
    // Set to 0
    for (i = 0; i < rem; i++){
      data[data_len-1-i] = 0x00;
    }
    // Pad to 4-byte word
    padded_data_len = data_len+(FLASH_WRITESIZE-rem);
  } else {
    padded_data_len = data_len;
  }

  // Write full buffer of 4-byte words
  return FlashProgram((unsigned long *)data, page_addr, padded_data_len);
}


void boot_firmware(void)
{
  uart_write_str(UART2, (char *) fw_release_message_address);

  // Boot the firmware
    __asm(
    "LDR R0,=0x10001\n\t"
    "BX R0\n\t"
  );
}
//NOTE THAT: 
// 1) Module can either transmit or receive data
// 2) Buffer size of the module is 64Byte. Data greater than this will overflow

#define VERBOSE_EBYTE_MODULE true
#define NUMBER_OF_PACKAGE_BYTES 4 // Please consider that during fixed transmission, first 3 bytes are reserved
// pin close to antenna (7) is GND, (1): MO, (2): M1, (3): E32-RX, (4): E32-TX, (5): AUX, (6): VCC, (7): GND
#define EBYTE_E32_M0_PIN 2 
#define EBYTE_E32_M1_PIN 3
#define EBYTE_E32_RX_PIN 5  //Software serial TX
#define EBYTE_E32_TX_PIN 4  //Software serial RX
#define EBYTE_E32_AUX_PIN 6

#define NMOS_GATE_LED 11
#define DEFINED_DEVICE_ADDRESS 58427 //same for all the devices
#define DEFINED_DEVICE_ID 175 // unique to device

/* TODO: PUT COMMAND PACKAGE INDICATING WHICH BIT IS WHICH*/
#define UART_PARITY_MODE_8O1 1
#define UART_PARITY_MODE_8E1 2
#define UART_PARITY_MODE_8N1 3 // (SUGGESTED) both 0 and 3 can be used

#define UART_BAUD_MODE_1200 0
#define UART_BAUD_MODE_2400 1
#define UART_BAUD_MODE_4800 2
#define UART_BAUD_MODE_9600 3 // (SUGGESTED)
#define UART_BAUD_MODE_19200 4
#define UART_BAUD_MODE_38400 5
#define UART_BAUD_MODE_57600 6
#define UART_BAUD_MODE_115200 7

#define AIR_DATA_RATE_MODE_2400BPS 2 // (SUGGESTED) all 0, 1 and 2 can be used
#define AIR_DATA_RATE_MODE_4800BPS 3
#define AIR_DATA_RATE_MODE_9600BPS 4
#define AIR_DATA_RATE_MODE_19200BPS 5 // all 5, 6 and 7 can be used

#define TRANSMISSION_MODE_TRANSPARENT 0
#define TRANSMISSION_MODE_FIXED 1

#define IO_DRIVE_MODE_OPEN_DRAIN 0 // No pull-up or down by internal resistor
#define IO_DRIVE_MODE_ACTIVE 1 // (SUGGESTED) TX-RX are pulled-up and down by internal resistor

#define WIRELESS_WAKE_UP_MODE_250_MS 0 //(SUGGESTED)
#define WIRELESS_WAKE_UP_MODE_500_MS 1 
#define WIRELESS_WAKE_UP_MODE_750_MS 2
#define WIRELESS_WAKE_UP_MODE_1000_MS 3 
#define WIRELESS_WAKE_UP_MODE_1250_MS 4 
#define WIRELESS_WAKE_UP_MODE_1500_MS 5 
#define WIRELESS_WAKE_UP_MODE_1750_MS 6 
#define WIRELESS_WAKE_UP_MODE_2000_MS 7 

#define FEC_MODE_NO 0
#define FEC_MODE_YES 1 // (SUGGESTED)

#define POWER_MODE_20Dbm 0
#define POWER_MODE_17Dbm 1
#define POWER_MODE_14Dbm 2
#define POWER_MODE_10Dbm 3

#define DEVICE_CHANNEL_E32_900T_868MHZ 6



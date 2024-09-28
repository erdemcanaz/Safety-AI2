#include <SoftwareSerial.h>
#include "config.h"  // when " is used rather than <, only current folder is looked for the header

SoftwareSerial EBYTESerial(EBYTE_E32_TX_PIN, EBYTE_E32_RX_PIN);  // software Rx, software Tx NOTE: should be 8N1 by default.

void setup() {
  delay(1000);

  Serial.begin(9600);
  EBYTESerial.begin(9600);
  pinMode(NMOS_GATE, OUTPUT);
  configure_ebyte_pins();
  set_ebyte_parameters();
}

uint8_t COMPUTER_LAST_COMMAND[6];  // DESTINATION_ID (x5 'ASCI 0-9') | ANIMATION_NO (x1 'ASCI 0-9)

void loop() {
  listen_and_execute_usb_serial_commands();
  listen_and_execute_lora_package();
}

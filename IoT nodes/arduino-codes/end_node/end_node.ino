#include <SoftwareSerial.h>
#include "config.h" // when " is used rather than <, only current folder is looked for the header

SoftwareSerial EBYTESerial(EBYTE_E32_TX_PIN, EBYTE_E32_RX_PIN);  // software Rx, software Tx NOTE: should be 8N1 by default.

void setup() {
  configure_ebyte_pins();

  Serial.begin(9600);
  EBYTESerial.begin(9600);  
}

void loop() {
 // set_ebyte_parameters();
 read_ebyte_parameters();

  
  delay(10000);
}









#define VERBOSE true
#define DEVICE_CHANNEL 12     //0-255, determines operation frequency -> 410+device_channel. 23 should be default (433MHz)
#define DEVICE_ADDRESS 3      //0-65535
#define UART_PARITY_MODE 3    //3->8N1
#define UART_BAUD_MODE 3      //3-> 9600BPS
#define AIR_DATA_RATE_MODE 2  //2-> 2.4Kbps
#define FIXED_TRANSMISSION_MODE 1
#define IO_DRIVE_MODE 1          //1-> TX & AUX: push-pull, RX: pull-up
#define WIRELESS_WAKE_UP_MODE 0  //-> 0.25kbps
#define FEC_MODE 1
#define POWER_MODE 0

uint8_t EBYTE_DESIRED_PARAMETERS[6]; // A byte array that stores EBYTE module desired parameters. Not guaranteed to be same with the module parameters
uint8_t EBYTE_RESPONSE_PARAMETERS[6]; // A byte array that stores EBYTE module response parameters. Guaranted to be same with the module parameters

void configure_ebyte_pins(){
  // pin close to antenna (7) is GND, (1): MO, (2): M1, (3): E32-RX, (4): E32-TX, (5): AUX, (6): VCC, (7): GND
  pinMode(EBYTE_E32_TX_PIN, INPUT);
  pinMode(EBYTE_E32_RX_PIN, OUTPUT);
  pinMode(EBYTE_E32_M0_PIN, OUTPUT);
  pinMode(EBYTE_E32_M1_PIN, OUTPUT);
  pinMode(EBYTE_E32_AUX_PIN, INPUT);
}

void read_ebyte_parameters(){
  /*
  This function reads Ebyte parameters and saves them to EBYTE_RESPONSE_PARAMETERS 
  if VERBOSE is set to true, the parameters are also printed
  */

  if(VERBOSE) Serial.println("\n___________\nReading Ebyte Parameters\nSetting device mode to M0=1, M1=1");
  digitalWrite(EBYTE_E32_M0_PIN, HIGH); 
  digitalWrite(EBYTE_E32_M1_PIN, HIGH);
  EBYTESerial.listen(); //When multiple software serials is used, only one can receive packages (i.e listened). ensure EBYTESerial is listening
  delay(1000);

  if(VERBOSE) Serial.println("Clearing EBYTESerial buffer");
  while(EBYTESerial.available())EBYTESerial.read();
  delay(250);

  if(VERBOSE) Serial.println("Sending three C1 (193)");
  //The binary format sends three C1s, and the module returns the saved parameters, which must be sent continuously.
  for (uint8_t i = 0; i < 3; i++) EBYTESerial.write(193);  //0xC1

  if(VERBOSE) Serial.println("Waiting for device response");
  delay(250);
  uint8_t response_index = 0;
  while(EBYTESerial.available()){
    uint8_t c = EBYTESerial.read();
    if (response_index < 6){
      EBYTE_RESPONSE_PARAMETERS[response_index] = c;
      if(VERBOSE) Serial.println("Response received           : ("+String(response_index) + ") - " +String(EBYTE_RESPONSE_PARAMETERS[response_index]));
    }else{
      if(VERBOSE) Serial.println("Exceeding Response received: ("+String(response_index) + ") - "+ String(c));
    }
    response_index++;
  }

}
void set_ebyte_parameters(){
  /*
  This function tries to set Ebyte parameters to desired values. The parameters are determines the operating mode, channel, address etc. 
  If 'VERBOSE' parameter is set to true, the desired and set parameters are also printed so that they can be checked.
  */
  
  if(VERBOSE) Serial.println("\n___________\nSetting and Reading Ebyte Parameters\nSetting device mode to M0=1, M1=1");
  digitalWrite(EBYTE_E32_M0_PIN, HIGH); 
  digitalWrite(EBYTE_E32_M1_PIN, HIGH);
  EBYTESerial.listen(); //When multiple software serials is used, only one can receive packages (i.e listened). ensure EBYTESerial is listening
  delay(1000);

  EBYTE_DESIRED_PARAMETERS[0] = 192;  //0xC0
  EBYTE_DESIRED_PARAMETERS[1] = DEVICE_ADDRESS >> 8;
  EBYTE_DESIRED_PARAMETERS[2] = DEVICE_ADDRESS % 256;
  EBYTE_DESIRED_PARAMETERS[3] = (UART_PARITY_MODE & B00000011) << 6;
  EBYTE_DESIRED_PARAMETERS[3] += (UART_BAUD_MODE & B00000111) << 3;
  EBYTE_DESIRED_PARAMETERS[3] += (AIR_DATA_RATE_MODE & B00000111);
  EBYTE_DESIRED_PARAMETERS[4] = (DEVICE_CHANNEL & B00011111);
  EBYTE_DESIRED_PARAMETERS[5] = (FIXED_TRANSMISSION_MODE & B00000001) << 7;
  EBYTE_DESIRED_PARAMETERS[5] += (IO_DRIVE_MODE & B00000001) << 6;
  EBYTE_DESIRED_PARAMETERS[5] += (FEC_MODE & B00000001) << 2;
  EBYTE_DESIRED_PARAMETERS[5] += (POWER_MODE & B00000011);

  if(VERBOSE) Serial.println("Clearing EBYTESerial buffer");
  while(EBYTESerial.available())EBYTESerial.read();
  
  for (uint8_t i = 0; i < 6; i++) {
    EBYTESerial.write(EBYTE_DESIRED_PARAMETERS[i]);
    //NOTE: never ever put another code block here, the bytes should be sent without any delay
  }
  if(VERBOSE){
    for(uint8_t i = 0 ; i <6 ; i++){
      Serial.println("Trying to set EBYTE register: ("+String(i)+") - " + String(EBYTE_DESIRED_PARAMETERS[i]));
    }
  }

  if(VERBOSE) Serial.println("Waiting for device response");
  delay(250);
  uint8_t response_index = 0;
  while(EBYTESerial.available()){
    uint8_t c = EBYTESerial.read();
    if (response_index < 6){
      EBYTE_RESPONSE_PARAMETERS[response_index] = c;
      if(VERBOSE) Serial.println("Response received           : ("+String(response_index) + ") - " +String(EBYTE_RESPONSE_PARAMETERS[response_index]));
    }else{
      if(VERBOSE) Serial.println("Exceeding Response received: ("+String(response_index) + ") - "+ String(c));
    }
    response_index++;
  }
}



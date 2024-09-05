const uint16_t DEVICE_ADDRESS            = 58427;      //0-65535. The 58427 is randomly picked to ensure there is no address collision with 3rd parties. Any number in this interval is accepted.
const uint8_t DEVICE_CHANNEL            = 23;     //0-255, determines operation frequency -> 410+device_channel. 23 should be default (433MHz)
const uint8_t UART_PARITY_MODE          = UART_PARITY_MODE_8N1;
const uint8_t UART_BAUD_MODE            = UART_BAUD_MODE_9600;      
const uint8_t AIR_DATA_RATE_MODE        = AIR_DATA_RATE_MODE_2400BPS;
const uint8_t TRANSMISSION_MODE         = TRANSMISSION_MODE_FIXED;
const uint8_t IO_DRIVE_MODE             = IO_DRIVE_MODE_ACTIVE;         
const uint8_t WIRELESS_WAKE_UP_MODE     = WIRELESS_WAKE_UP_MODE_250_MS;
const uint8_t FEC_MODE                  = FEC_MODE_YES;
const uint8_t POWER_MODE                = POWER_MODE_20Dbm;

uint8_t EBYTE_DESIRED_PARAMETERS[6]; // A byte array that stores EBYTE module desired parameters. Not guaranteed to be same with the module parameters
uint8_t EBYTE_RESPONSE_PARAMETERS[6]; // A byte array that stores EBYTE module response parameters. Guaranted to be same with the module parameters
uint8_t BUFFER_TRANSMIT_PACKAGE[NUMBER_OF_PACKAGE_BYTES]; 
uint8_t BUFFER_RECEIVE_PACKAGE[NUMBER_OF_PACKAGE_BYTES];

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
  if VERBOSE_EBYTE_MODULE is set to true, the parameters are also printed
  */

  if(VERBOSE_EBYTE_MODULE) Serial.println("\n___________\nReading Ebyte Parameters\nSetting device mode to M0=1, M1=1");
  digitalWrite(EBYTE_E32_M0_PIN, HIGH); 
  digitalWrite(EBYTE_E32_M1_PIN, HIGH);
  EBYTESerial.listen(); //When multiple software serials is used, only one can receive packages (i.e listened). ensure EBYTESerial is listening
  delay(1000);

  if(VERBOSE_EBYTE_MODULE) Serial.println("Clearing EBYTESerial buffer");
  while(EBYTESerial.available())EBYTESerial.read();
  delay(250);

  //The binary format sends three C1s, and the module returns the saved parameters
  if(VERBOSE_EBYTE_MODULE) Serial.println("Sending three C1 (193)");
  for (uint8_t i = 0; i < 3; i++) EBYTESerial.write(193);  //0xC1

  if(VERBOSE_EBYTE_MODULE) Serial.println("Waiting for device response");
  delay(250);
  uint8_t response_index = 0;
  while(EBYTESerial.available()){
    uint8_t c = EBYTESerial.read();
    if (response_index < 6){
      EBYTE_RESPONSE_PARAMETERS[response_index] = c;
      if(VERBOSE_EBYTE_MODULE) Serial.println("Response received           : ("+String(response_index) + ") - " +String(EBYTE_RESPONSE_PARAMETERS[response_index]));
    }else{
      if(VERBOSE_EBYTE_MODULE) Serial.println("Exceeding Response received: ("+String(response_index) + ") - "+ String(c));
    }
    response_index++;
  }

}

void set_ebyte_parameters(){
  /*
  This function tries to set Ebyte parameters to desired values. The parameters are determines the operating mode, channel, address etc. 
  If 'VERBOSE_EBYTE_MODULE' parameter is set to true, the desired and set parameters are also printed so that they can be checked.
  */
  
  if(VERBOSE_EBYTE_MODULE) Serial.println("\n___________\nSetting and Reading Ebyte Parameters\nSetting device mode to M0=1, M1=1");
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
  EBYTE_DESIRED_PARAMETERS[5] = (TRANSMISSION_MODE & B00000001) << 7;
  EBYTE_DESIRED_PARAMETERS[5] += (IO_DRIVE_MODE & B00000001) << 6;
  EBYTE_DESIRED_PARAMETERS[5] += (FEC_MODE & B00000001) << 2;
  EBYTE_DESIRED_PARAMETERS[5] += (POWER_MODE & B00000011);

  if(VERBOSE_EBYTE_MODULE) Serial.println("Clearing EBYTESerial buffer");
  while(EBYTESerial.available())EBYTESerial.read();
  
  for (uint8_t i = 0; i < 6; i++) {
    EBYTESerial.write(EBYTE_DESIRED_PARAMETERS[i]);
    //NOTE: never ever put another code block here, the bytes should be sent without any delay
  }
  if(VERBOSE_EBYTE_MODULE){
    for(uint8_t i = 0 ; i <6 ; i++){
      Serial.println("Trying to set EBYTE register: ("+String(i)+") - " + String(EBYTE_DESIRED_PARAMETERS[i]));
    }
  }

  if(VERBOSE_EBYTE_MODULE) Serial.println("Waiting for device response");
  delay(250);
  uint8_t response_index = 0;
  while(EBYTESerial.available()){
    uint8_t c = EBYTESerial.read();
    if (response_index < 6){
      EBYTE_RESPONSE_PARAMETERS[response_index] = c;
      if(VERBOSE_EBYTE_MODULE) Serial.println("Response received           : ("+String(response_index) + ") - " +String(EBYTE_RESPONSE_PARAMETERS[response_index]));
    }else{
      if(VERBOSE_EBYTE_MODULE) Serial.println("Exceeding Response received: ("+String(response_index) + ") - "+ String(c));
    }
    response_index++;
  }
}

bool transmit_fixed_package(){
  digitalWrite(EBYTE_E32_M0_PIN, LOW); 
  digitalWrite(EBYTE_E32_M1_PIN, LOW);

  //First 3 bytes are reserved
  BUFFER_TRANSMIT_PACKAGE[0]=DEVICE_ADDRESS>>8;    // HIGH-BYTE
  BUFFER_TRANSMIT_PACKAGE[1]=DEVICE_ADDRESS & 255; // LOW-BYTE
  BUFFER_TRANSMIT_PACKAGE[2]=DEVICE_CHANNEL;

  //Set remaining bytes
  BUFFER_TRANSMIT_PACKAGE[3]= 3;

  //TX package to EBYTE buffer so that package can be transmitted
  for(uint8_t i = 0; i < NUMBER_OF_PACKAGE_BYTES;i++){
    EBYTESerial.write(BUFFER_TRANSMIT_PACKAGE[i]);
  }
  while(digitalRead(EBYTE_E32_AUX_PIN)==0); // AUX pin is 0 during transmission
  Serial.println("T");
}


bool listen_package(){
  digitalWrite(EBYTE_E32_M0_PIN, LOW); 
  digitalWrite(EBYTE_E32_M1_PIN, LOW);

  if (EBYTESerial.available()==0)return;
  
  delay(250);
  while(EBYTESerial.available()) Serial.println(EBYTESerial.read());
  Serial.println("R");
}



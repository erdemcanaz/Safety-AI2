
const uint16_t DEVICE_ID = DEFINED_DEVICE_ID;
const uint16_t DEVICE_ADDRESS = DEFINED_DEVICE_ADDRESS;         //0-65535. The 58427 is randomly picked to ensure there is no address collision with 3rd parties. Any number in this interval is accepted.
const uint8_t DEVICE_CHANNEL = DEVICE_CHANNEL_E32_900T_868MHZ;  //0-255, determines operation frequency -> 410+device_channel. 23 should be default (433MHz)
const uint8_t UART_PARITY_MODE = UART_PARITY_MODE_8N1;
const uint8_t UART_BAUD_MODE = UART_BAUD_MODE_9600;
const uint8_t AIR_DATA_RATE_MODE = AIR_DATA_RATE_MODE_2400BPS;
const uint8_t TRANSMISSION_MODE = TRANSMISSION_MODE_FIXED;
const uint8_t IO_DRIVE_MODE = IO_DRIVE_MODE_ACTIVE;
const uint8_t WIRELESS_WAKE_UP_MODE = WIRELESS_WAKE_UP_MODE_250_MS;
const uint8_t FEC_MODE = FEC_MODE_YES;
const uint8_t POWER_MODE = POWER_MODE_20Dbm;

uint8_t EBYTE_DESIRED_PARAMETERS[6];   // A byte array that stores EBYTE module desired parameters. Not guaranteed to be same with the module parameters
uint8_t EBYTE_RESPONSE_PARAMETERS[6];  // A byte array that stores EBYTE module response parameters. Guaranted to be same with the module parameters
uint8_t BUFFER_TRANSMIT_PACKAGE[NUMBER_OF_PACKAGE_BYTES];
uint8_t BUFFER_RECEIVE_PACKAGE[NUMBER_OF_PACKAGE_BYTES - 3];

void configure_ebyte_pins() {
  // pin close to antenna (7) is GND, (1): MO, (2): M1, (3): E32-RX, (4): E32-TX, (5): AUX, (6): VCC, (7): GND
  pinMode(EBYTE_E32_TX_PIN, INPUT);
  pinMode(EBYTE_E32_RX_PIN, OUTPUT);
  pinMode(EBYTE_E32_M0_PIN, OUTPUT);
  pinMode(EBYTE_E32_M1_PIN, OUTPUT);
  pinMode(EBYTE_E32_AUX_PIN, INPUT);
}

void read_ebyte_parameters() {
  /*
  This function reads Ebyte parameters and saves them to EBYTE_RESPONSE_PARAMETERS 
  if VERBOSE_EBYTE_MODULE is set to true, the parameters are also printed
  */

  if (VERBOSE_EBYTE_MODULE) Serial.println("\n___________\nReading Ebyte Parameters\nSetting device mode to M0=1, M1=1");
  digitalWrite(EBYTE_E32_M0_PIN, HIGH);
  digitalWrite(EBYTE_E32_M1_PIN, HIGH);
  EBYTESerial.listen();  //When multiple software serials is used, only one can receive packages (i.e listened). ensure EBYTESerial is listening
  delay(1000);

  if (VERBOSE_EBYTE_MODULE) Serial.println("Clearing EBYTESerial buffer");
  while (EBYTESerial.available()) EBYTESerial.read();
  delay(250);

  //The binary format sends three C1s, and the module returns the saved parameters
  if (VERBOSE_EBYTE_MODULE) Serial.println("Sending three C1 (193)");
  for (uint8_t i = 0; i < 3; i++) EBYTESerial.write(193);  //0xC1

  if (VERBOSE_EBYTE_MODULE) Serial.println("Waiting for device response");
  delay(250);
  uint8_t response_index = 0;
  while (EBYTESerial.available()) {
    uint8_t c = EBYTESerial.read();
    if (response_index < 6) {
      EBYTE_RESPONSE_PARAMETERS[response_index] = c;
      if (VERBOSE_EBYTE_MODULE) Serial.println("Response received           : (" + String(response_index) + ") - " + String(EBYTE_RESPONSE_PARAMETERS[response_index]));
    } else {
      if (VERBOSE_EBYTE_MODULE) Serial.println("Exceeding Response received: (" + String(response_index) + ") - " + String(c));
    }
    response_index++;
  }
}

void set_ebyte_parameters() {
  /*
  This function tries to set Ebyte parameters to desired values. The parameters are determines the operating mode, channel, address etc. 
  If 'VERBOSE_EBYTE_MODULE' parameter is set to true, the desired and set parameters are also printed so that they can be checked.
  */

  if (VERBOSE_EBYTE_MODULE) Serial.println("\n___________\nSetting and Reading Ebyte Parameters\nSetting device mode to M0=1, M1=1");
  digitalWrite(EBYTE_E32_M0_PIN, HIGH);
  digitalWrite(EBYTE_E32_M1_PIN, HIGH);
  EBYTESerial.listen();  //When multiple software serials is used, only one can receive packages (i.e listened). ensure EBYTESerial is listening
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

  if (VERBOSE_EBYTE_MODULE) Serial.println("Clearing EBYTESerial buffer");
  while (EBYTESerial.available()) EBYTESerial.read();

  for (uint8_t i = 0; i < 6; i++) {
    EBYTESerial.write(EBYTE_DESIRED_PARAMETERS[i]);
    //NOTE: never ever put another code block here, the bytes should be sent without any delay
  }
  if (VERBOSE_EBYTE_MODULE) {
    for (uint8_t i = 0; i < 6; i++) {
      Serial.println("Trying to set EBYTE register: (" + String(i) + ") - " + String(EBYTE_DESIRED_PARAMETERS[i]));
    }
  }

  if (VERBOSE_EBYTE_MODULE) Serial.println("Waiting for device response");
  delay(250);
  uint8_t response_index = 0;
  while (EBYTESerial.available()) {
    uint8_t c = EBYTESerial.read();
    if (response_index < 6) {
      EBYTE_RESPONSE_PARAMETERS[response_index] = c;
      if (VERBOSE_EBYTE_MODULE) Serial.println("Response received           : (" + String(response_index) + ") - " + String(EBYTE_RESPONSE_PARAMETERS[response_index]));
    } else {
      if (VERBOSE_EBYTE_MODULE) Serial.println("Exceeding Response received: (" + String(response_index) + ") - " + String(c));
    }
    response_index++;
  }
}

bool transmit_fixed_package() {
  // This function broadcasts the 'BUFFER_TRANSMIT_PACKAGE' content over the Ebyte device
  // NOTE: this function assumes that 'BUFFER_TRANSMIT_PACKAGE' content is properly set, then broadcasts it content
  digitalWrite(EBYTE_E32_M0_PIN, LOW);
  digitalWrite(EBYTE_E32_M1_PIN, LOW);

  //First 3 bytes are reserved
  BUFFER_TRANSMIT_PACKAGE[0] = DEVICE_ADDRESS >> 8;   // HIGH-BYTE
  BUFFER_TRANSMIT_PACKAGE[1] = DEVICE_ADDRESS & 255;  // LOW-BYTE
  BUFFER_TRANSMIT_PACKAGE[2] = DEVICE_CHANNEL;

  //TX package to EBYTE buffer so that package can be transmitted
  for (uint8_t i = 0; i < NUMBER_OF_PACKAGE_BYTES; i++) {
    EBYTESerial.write(BUFFER_TRANSMIT_PACKAGE[i]);
  }
  while (digitalRead(EBYTE_E32_AUX_PIN) == 0)
    ;  // AUX pin is 0 during transmission

  Serial.println("T");
}

void animate_alert(uint8_t animation_no) {  //5 second 0 Hz blink
    if (animation_no == 0) {  //5 second 0 Hz blink
      digitalWrite(NMOS_GATE, HIGH);
      delay(5000);
      digitalWrite(NMOS_GATE, LOW);
    } else if (animation_no == 1) {  //5 second 0.5 Hz blink
      for (uint8_t i = 0; i < 3; i++) {
        digitalWrite(NMOS_GATE, HIGH);
        delay(1000);
        digitalWrite(NMOS_GATE, LOW);
        delay(1000);
      }
    } else if (animation_no == 2) {  //5 second 1 Hz blink
      for (uint8_t i = 0; i < 5; i++) {
        digitalWrite(NMOS_GATE, HIGH);
        delay(500);
        digitalWrite(NMOS_GATE, LOW);
        delay(500);
      }
    } else if (animation_no == 3) {  //5 second 4 Hz blink
      for (uint8_t i = 0; i < 20; i++) {
        digitalWrite(NMOS_GATE, HIGH);
        delay(125);
        digitalWrite(NMOS_GATE, LOW);
        delay(125);
      }
    } else if (animation_no == 4) {  //15 second 0 Hz blink
      digitalWrite(NMOS_GATE, HIGH);
      delay(15000);
      digitalWrite(NMOS_GATE, LOW);
    } else if (animation_no == 5) {  //15 second 0.5 Hz blink
      for (uint8_t i = 0; i < 8; i++) {
        digitalWrite(NMOS_GATE, HIGH);
        delay(1000);
        digitalWrite(NMOS_GATE, LOW);
        delay(1000);
      }
    } else if (animation_no == 6) {  //15 second 1 Hz blink
      for (uint8_t i = 0; i < 15; i++) {
        digitalWrite(NMOS_GATE, HIGH);
        delay(500);
        digitalWrite(NMOS_GATE, LOW);
        delay(500);
      }
    } else if (animation_no == 7) {  //15 second 4 Hz blink
      for (uint8_t i = 0; i < 75; i++) {
        digitalWrite(NMOS_GATE, HIGH);
        delay(125);
        digitalWrite(NMOS_GATE, LOW);
        delay(125);
      }
    }else{
      //DO NOTHING
    }
}

void listen_and_execute_usb_serial_commands() {
  //This function checks if a command is sent by the computer, then executes it
  // XXXXXY -> 001785 -> ID 00178, ANIMATION_NO 5
  if (Serial.available() > 0) {
    //(1)
    delay(50);  // To ensure all data is in the buffer
    if (Serial.available() >= NUMBER_OF_PACKAGE_BYTES - 3) {
      for (uint8_t i = 3; i < NUMBER_OF_PACKAGE_BYTES; i++) {  // DESTINATION_ID_STR (x5 'ASCI 0-9') | BOUNCE_COUNT (x1 'ASCI 0-9) & First 3 bytes are reserved, start from fourth byte
        uint8_t c = Serial.read();
        BUFFER_TRANSMIT_PACKAGE[i] = c;
      }
      //(2)
      transmit_fixed_package();
    }
    //(3)
    while (Serial.available() > 0) Serial.read();  // Empty the buffer
  }
}

void listen_and_execute_lora_package() {
  digitalWrite(EBYTE_E32_M0_PIN, LOW);
  digitalWrite(EBYTE_E32_M1_PIN, LOW);

  if (EBYTESerial.available() == 0) return;

  // (1, R):Save package, if not proper, return. After saving, empty the buffer.
  delay(50);  // To ensure all data is in the buffer
  if (EBYTESerial.available() >= NUMBER_OF_PACKAGE_BYTES - 3) {
    for (uint8_t i = 0; i < NUMBER_OF_PACKAGE_BYTES - 3; i++) {  // DESTINATION_ID_STR (x5 'ASCI 0-9') | ANIMATION_NO (x1 'ASCI 0-9) & First 3 bytes are reserved, start from fourth byte
      uint8_t c = EBYTESerial.read();
      if (c < '0' || '9' < c) {  // All bytes must be '0-9', otherwise clear buffer and exit
        while (EBYTESerial.available() > 0) EBYTESerial.read();
        return;
      }
      BUFFER_RECEIVE_PACKAGE[i] = c;
    }
  }

  // (2): Parse Package (HARDCODED, should match with the package format
  // DESTINATION_ID_STR (x5 'ASCI 0-9') | ANIMATION_NO (x1 'ASCI 0-9) & First 3 bytes are reserved, start from fourth byte
  uint8_t animation_no = BUFFER_RECEIVE_PACKAGE[5] - '0';
  uint16_t destination_id = 0;
  destination_id = destination_id + 10000 * (BUFFER_RECEIVE_PACKAGE[0] - '0');
  destination_id = destination_id + 1000 * (BUFFER_RECEIVE_PACKAGE[1] - '0');
  destination_id = destination_id + 100 * (BUFFER_RECEIVE_PACKAGE[2] - '0');
  destination_id = destination_id + 10 * (BUFFER_RECEIVE_PACKAGE[3] - '0');
  destination_id = destination_id + (BUFFER_RECEIVE_PACKAGE[4] - '0');

  // (3, R): Check if destination is this. If yes, animate
  if (destination_id == DEFINED_DEVICE_ID) {
    animate_alert(animation_no);
  }
  while (EBYTESerial.available() > 0) EBYTESerial.read();
  return;
}

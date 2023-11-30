#include <Arduino.h>

bool instructionReceivedFlag = false;

void clearSerialBuffer() {
  while (Serial.available() > 0) { 
    Serial.read(); // Read and discard the incoming byte
  }
}

void setup() {
  Serial.begin(115200);
}

void loop() {
  while (instructionReceivedFlag == false) {
    if (Serial.available() >= 4) { // Check if 4 bytes are available
      uint8_t values[4];
      for (int i = 0; i < 4; i++) {
        values[i] = Serial.read();
      }

    // Send data back as a hex string
    for (int i = 0; i < 4; i++) {
      if (values[i] < 16) {
        Serial.print('0'); // Print leading zero for values less than 16
      }
      Serial.print(values[i], HEX);
    }
    Serial.println(); // End the line
    delay(1000);
    }
  }
}
#include <Arduino.h>

#define PWM_PIN 10
#define ADC_PIN A0

int current10bit;
uint8_t current8bit;
uint8_t voltage;

void clearSerialBuffer() {
  while (Serial.available() > 0) { 
    Serial.read(); // Read and discard the incoming byte
  }
}

void setup() {
  TCCR1B = TCCR1B & B11111000 | B00000001; //Set dividers to change PWM frequency 3.1 khz
  Serial.begin(115200);
  pinMode(PWM_PIN,OUTPUT);
  pinMode(ADC_PIN,INPUT);
}

void loop() {
  if (Serial.available() > 0) {
    voltage = Serial.read();
    current10bit = analogRead(ADC_PIN);
    current8bit = current10bit >> 2;
    Serial.println(current8bit);
    analogWrite(PWM_PIN, voltage);
  }

  /* // Send data back as a hex string
  for (int i = 0; i < 4; i++) {
    if (values[i] < 16) {
      Serial.print('0'); // Print leading zero for values less than 16
    }
    Serial.print(values[i], HEX);
  }
  Serial.println(); // End the line
  delay(1000); */
}
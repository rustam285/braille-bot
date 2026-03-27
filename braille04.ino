const byte pinCount = 6;
const byte pins[pinCount] = {2, 3, 4, 5, 6, 7};
boolean states[pinCount];
unsigned long result;

void setup() {
  Serial.begin(9600);
  for (byte i = 0; i < pinCount; i++) {
    pinMode(pins[i], INPUT);
  }
}

void loop() {
  result = 0;
  unsigned long multiplier = 1;

  for (byte i = 0; i < pinCount; i++) {
    states[i] = digitalRead(pins[i]) == HIGH;
    result += states[i] * multiplier;
    multiplier *= 10;
  }

  Serial.println(result);
  delay(2000);
}

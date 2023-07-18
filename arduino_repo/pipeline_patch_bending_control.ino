const int pumpRPin = 10;  
const int pumpPin = 11;  
const int valvePin = 12; 

String command = "";
void setup() {
  // Initialize serial and wait for port to open:
  Serial.begin(9600);
  pinMode(pumpPin, OUTPUT); 
  pinMode(pumpRPin, OUTPUT);  
  pinMode(valvePin, OUTPUT);
}
int blow = 0;
int hold = 0;
int release = 0;
int stop = 0;
void loop() {
  if (Serial.available() > 0) {
    int val = char(Serial.read()) - '0';
    if(val == 0){ // blow
      blow = 1;
      hold = 0;
      release = 0;
      stop = 0;
      Serial.write("BLOW\n");
    }
    if(val == 1){ // hold
      blow = 0;
      hold = 1;
      release = 0;
      stop = 0;
      Serial.write("HOLD\n");
    }
    if(val == 2){ // release
      blow = 0;
      hold = 0;
      release = 1;
      stop = 0;
      Serial.write("RELEASE\n");
    }
    if(val == 3){ // stop
      blow = 0;
      hold = 0;
      release = 0;
      stop = 1;
      Serial.write("STOP\n");
    }
  }
  if(blow == 1){
    analogWrite(pumpRPin, 0);
    analogWrite(valvePin, 255);
    analogWrite(pumpPin, 255);
    delay(30);
    analogWrite(pumpPin, 0);
    delay(50);
  }
  if(hold == 1){
    analogWrite(pumpRPin, 0);
    analogWrite(valvePin, 255);
    analogWrite(pumpPin, 0);
  }
  if(release == 1){
    analogWrite(pumpRPin, 255);
    analogWrite(valvePin, 0);
    analogWrite(pumpPin, 0);
  }
  if(stop == 1){
    analogWrite(valvePin, 0);
    analogWrite(pumpPin, 0);
    analogWrite(pumpRPin, 0);
  }
}




// // wifi connect init CM
// char ssid[] = "NETGEAR91";        // your network SSID (name)
// char pass[] = "basicmint606";  // your network password

const int pumpRPin = 9;  
const int pumpPin = 11;  
const int valvePin = 12;
const int valve2Pin = 8;  
float air_blow_time_radial = 0.5;

void pump_on() {
  analogWrite(pumpPin, 255);
  delay(60*air_blow_time_radial);
  analogWrite(pumpPin, 0);
  delay(60*(1-air_blow_time_radial));
}

String command = "";
void setup() {
  // Initialize serial and wait for port to open:
  Serial.begin(9600);
  pinMode(pumpPin, OUTPUT); 
  pinMode(pumpRPin, OUTPUT);  
  pinMode(valvePin, OUTPUT);
  pinMode(valve2Pin, OUTPUT);
}
int blow1 = 0;
int release1 = 0;
int blow2 = 0;
int release2 = 0;
int stop = 0;
int timer = -1;
unsigned long startT1 = 0;
unsigned long startT2 = 0;
void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    int val = input.charAt(0) - '0';
    if(input.length() > 1){
      input.trim();
      if(input.startsWith("abt")){ // change the air blowing energy
        int index = input.indexOf(' ');
        String content = input.substring(index+1, input.length());
        air_blow_time_radial = constrain(content.toFloat(), 0, 1);
        Serial.print("Successfully changed the air_blow_time_radial to ");
        Serial.println(air_blow_time_radial);
      }
      if(input.startsWith("timer")){ // change the air blowing energy
        int index = input.indexOf(' ');
        String content = input.substring(index+1, input.length());
        timer = constrain(content.toInt(), -1, 100); // -1 is off, any positive is on which blow for timer time
        Serial.print("Successfully changed the timer to ");
        Serial.println(timer);
      }
    } 
    if(val == 1){ // blow1
      blow1 = 1;
      release1 = 0;
      stop = 0;
      startT1 = millis();
      Serial.write("BLOW1\n");
    }
    if(val == 2){ // release1
      blow1 = 0;
      release1 = 1;
      stop = 0;
      Serial.write("RELEASE1\n");
    }
    if(val == 3){ // stop
      blow1 = 0;
      release1 = 0;
      blow2 = 0;
      release2 = 0;
      stop = 1;
      Serial.write("STOP\n");
    }
    if(val == 4){ // blow2 ***change to 1 for blowing both patch***
      blow2 = 1;
      release2 = 0;
      stop = 0;
      startT2 = millis();
      Serial.write("BLOW2\n");
    }
    if(val == 5){ // release2
      blow2 = 0;
      release2 = 1;
      stop = 0;
      Serial.write("RELEASE2\n");
    }
  }
  if(blow1 == 1){
    analogWrite(pumpRPin, 0);
    analogWrite(valvePin, 255);
    int interval = (millis()- startT1)/1000;
    Serial.println(interval);
    if(timer == -1 || interval < timer){
      pump_on();
    }
  }
  if(release1 == 1){
    analogWrite(pumpRPin, 255);
    analogWrite(valvePin, 0);
    analogWrite(pumpPin, 0);
  }
  if(blow2 == 1){
    analogWrite(pumpRPin, 0);
    analogWrite(valve2Pin, 255);
    int interval = (millis()- startT2)/1000;
    Serial.println(interval);
    if(timer == -1 || interval < timer){
      pump_on();
    }
  }
  if(release2 == 1){
    analogWrite(pumpRPin, 255);
    analogWrite(valve2Pin, 0);
    analogWrite(pumpPin, 0);
  }
  if(stop == 1){
    analogWrite(valvePin, 0);
    analogWrite(valve2Pin, 0);
    analogWrite(pumpPin, 0);
    analogWrite(pumpRPin, 0);
  }
}


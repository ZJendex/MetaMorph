

  // // wifi connect init CM
  // char ssid[] = "NETGEAR91";        // your network SSID (name)
  // char pass[] = "basicmint606";  // your network password

  const int pumpRPin = 9;  
  const int pumpPin = 11;  
  const int valvePin = 12;
  const int valve2Pin = 8;  
  const int holdPin = 3; 
  const int hold2Pin = 4;   
  float air_blow_time_radial = 0.75;
  int p1 = 0;
  int p2 = 0;
  void pump_on() {
    analogWrite(pumpPin, 255);
    delay(60*air_blow_time_radial);
    analogWrite(pumpPin, 0);
    delay(60*(1-air_blow_time_radial));
  }
  void pumpR_on() {
    analogWrite(pumpRPin, 255);
    delay(60*air_blow_time_radial);
    analogWrite(pumpRPin, 0);
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
    pinMode(holdPin, OUTPUT);
    pinMode(hold2Pin, OUTPUT);
  }
  int blow1 = 0;
  int hold1 = 0;
  int release1 = 0;
  int blow2 = 0;
  int hold2 = 0;
  int release2 = 0;
  int stop = 0;
  int timer = -1;
  unsigned long startT1 = 0;
  unsigned long startT2 = 0;

  void loop() {
    if (Serial.available() > 0) {
      String input = Serial.readStringUntil('\n');
      int val = input.charAt(0) - '0';
      int val1 = -1;
      int val2 = -1;
      if(input.length() == 2){
        val1 = input.charAt(0) - '0';
        val2 = input.charAt(1) - '0';
        if((val1 == 1 || val1 == 7 || val1 == 2) && (val2 == 4 || val2 == 5 || val2 == 6)){
          // syn control good to go
        } else{
          val = 3;
          val1 = -1;
          val2 = -1;
        }
      }
      if(input.length() > 1){
        input.trim();
        if(input.startsWith("abt")){ // change the air blowing energy
          int index = input.indexOf(' ');
          String content = input.substring(index+1, input.length());
          air_blow_time_radial = constrain(content.toFloat(), 0, 1);
          Serial.print("Successfully changed the air_blow_time_radial to ");
          Serial.println(air_blow_time_radial);
        }
        if(input.startsWith("timer")){ // change the air blowing time
          int index = input.indexOf(' ');
          String content = input.substring(index+1, input.length());
          timer = constrain(content.toInt(), -1, 100); // -1 is off, any positive is on which blow for timer time
          Serial.print("Successfully changed the timer to ");
          Serial.println(timer);
        }
      } 
      if(val == 1 || val1 == 1){ // blow1
        blow1 = 1;
        release1 = 0;
        hold1 = 0;
        stop = 0;
        startT1 = millis();
        Serial.write("BLOW1\n");
      }
      if(val == 2 || val1 == 2){ // release1
        blow1 = 0;
        release1 = 1;
        hold1 = 0;
        stop = 0;
        startT1 = millis();
        Serial.write("RELEASE1\n");
      }
      if(val == 3){ // stop
        blow1 = 0;
        release1 = 0;
        hold1 = 0;
        blow2 = 0;
        release2 = 0;
        hold2 = 0;
        stop = 1;
        Serial.write("STOP\n");
      }
      if(val == 4 || val2 == 4){ // blow2 ***change to 1 for blowing both patch***
        blow2 = 1;
        release2 = 0;
        hold2 = 0;
        stop = 0;
        startT2 = millis();
        Serial.write("BLOW2\n");
      }
      if(val == 5 || val2 == 5){ // release2
        blow2 = 0;
        release2 = 1;
        hold2 = 0;
        stop = 0;
        startT2 = millis();
        Serial.write("RELEASE2\n");
      }
      if(val == 6 || val2 == 6){ // hold2
        blow2 = 0;
        release2 = 0;
        hold2 = 1;
        stop = 0;
        Serial.write("HOLD2\n");
      }
      if(val == 7 || val1 == 7){ // hold1
        blow1 = 0;
        release1 = 0;
        hold1 = 1;
        stop = 0;
        Serial.write("HOLD1\n");
      }
    }
    if(blow1 == 1){
      // int interval = (millis()- startT1)/1000;
      // if(timer == -1 || interval < timer){
      //   analogWrite(pumpRPin, 0);
      //   analogWrite(valvePin, 255);
      //   pump_on();
      // }
      analogWrite(pumpRPin, 0);
      analogWrite(valvePin, 255);
      analogWrite(holdPin, 255);
      pump_on();
    }
    if(hold1 == 1){
      analogWrite(pumpRPin, 0);
      analogWrite(holdPin, 0);
      analogWrite(valvePin, 0);
      analogWrite(pumpPin, 0);
    }
    if(release1 == 1){
      // int interval = (millis()- startT1)/1000;
      // if(timer == -1 || interval < timer){
      //   pumpR_on();
      //   analogWrite(valvePin, 0);
      //   analogWrite(pumpPin, 0);
      // } else{
      //   analogWrite(pumpRPin, 0);
      //   analogWrite(valvePin, 255);
      //   analogWrite(pumpPin, 0);
      // }
      analogWrite(valvePin, 0);
      analogWrite(pumpPin, 0);
      analogWrite(holdPin, 255);
      pumpR_on();
    }
    if(blow2 == 1){
      analogWrite(pumpRPin, 0);
      analogWrite(valve2Pin, 255);
      analogWrite(hold2Pin, 255);
      pump_on();
      // int interval = (millis()- startT2)/1000;
      // if(timer == -1 || interval > 0 && interval < timer){
      //   pump_on();
      // }
    }
    if(hold2 == 1){
      analogWrite(pumpRPin, 0);
      analogWrite(hold2Pin, 0);
      analogWrite(valve2Pin, 0);
      analogWrite(pumpPin, 0);
    }
    if(release2 == 1){
      // int interval = (millis()- startT2)/1000;
      // if(timer == -1 || interval > 0 && interval < timer){
      //   pumpR_on();
      //   analogWrite(valve2Pin, 0);
      //   analogWrite(pumpPin, 0);
      // } else{
      //   analogWrite(pumpRPin, 0);
      //   analogWrite(valve2Pin, 255);
      //   analogWrite(pumpPin, 0);
      // }
      analogWrite(valve2Pin, 0);
      analogWrite(pumpPin, 0);
      analogWrite(hold2Pin, 255);
      pumpR_on();
    }
    if(stop == 1){
      analogWrite(valvePin, 0);
      analogWrite(valve2Pin, 0);
      analogWrite(pumpPin, 0);
      analogWrite(pumpRPin, 0);
      analogWrite(holdPin, 0);
      analogWrite(hold2Pin, 0);
    }
  }


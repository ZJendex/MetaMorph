#include <SPI.h>
#include <WiFiNINA.h>
#include <WiFiUdp.h>
#include <Arduino_LSM6DS3.h> // IMU
#include <PID_v1.h> // PID control

// // wifi connect init CM
// char ssid[] = "NETGEAR91";        // your network SSID (name)
// char pass[] = "basicmint606";  // your network password

// wifi connect init ASUS
char ssid[] = "ASUS_A0_2G";        // your network SSID (name)
char pass[] = "password123";  // your network password

// local computer ip address
int ip1 = 192;
int ip2 = 168;
int ip3 = 1;
int ip4 = 150;

int status = WL_IDLE_STATUS;

WiFiUDP Udp;

unsigned int localPort = 2391; // local port to listen for UDP packets
int remotePort = 2391; // replace with your computer's listening port

char packetBuffer[255]; // buffer to hold incoming packets
char ReplyBuffer[] = "hello world"; // a string to send back
char StartCode[] = "hi"; // the passcode send to local computer to start the control terminal


// Motor control pins init
int directionPinR = 12;
int pwmPinR = 3;
int brakePinR = 9;

int directionPinL = 13;
int pwmPinL = 11;
int brakePinL = 8;

// int l_stop_time = -1;
// int r_stop_time = -1;

int speed = 255; // Motor speed (0-255)

// PID control init
// const double Kp = 2.0, Ki = 5.0, Kd = 1.0; // These values need to be tuned for your specific system
const double Kp = 6.0, Ki = 0.0, Kd = 0.0; // These values need to be tuned for your specific system
const int BASE_L_STOP_TIME = 6, BASE_R_STOP_TIME = 6; // Base stop times in ms
const int MIN_STOP_TIME = 1, MAX_STOP_TIME = 300; // Min and max stop times in ms

double Setpoint, Input, Output; // Setpoint, input, and output for the PID controller
int l_stop_time = BASE_L_STOP_TIME, r_stop_time = BASE_R_STOP_TIME; // Current stop times

// PID controller
PID myPID(&Input, &Output, &Setpoint, Kp, Ki, Kd, DIRECT);

String command = "";
void setup() {
  // Initialize serial and wait for port to open:
  Serial.begin(9600);

  // Set all the motor control pins as outputs
  pinMode(directionPinL, OUTPUT);
  pinMode(pwmPinL, OUTPUT);
  pinMode(brakePinL, OUTPUT);

  pinMode(directionPinR, OUTPUT);
  pinMode(pwmPinR, OUTPUT);
  pinMode(brakePinR, OUTPUT);

  // Check for the WiFi module:
  if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // don't continue
    while (true);
  }

  // Attempt to connect to the WiFi network:
  while (status != WL_CONNECTED) {
    Serial.print("Attempting to connect to network: ");
    Serial.println(ssid);
    // Connect to WPA/WPA2 network:
    status = WiFi.begin(ssid, pass);
    // wait 5 seconds for connection:
    delay(2000);
  }

  Serial.println("Connected to WiFi");
  Udp.begin(localPort);
  // Send the UDP message to start double-end comunication between arduino and local computer
  IPAddress remoteIp(ip1, ip2, ip3, ip4); // replace with your computer's IP address
  Udp.beginPacket(remoteIp, remotePort);
  Udp.write(StartCode);
  Udp.endPacket();
  Serial.print("Sent: ");
  Serial.println(StartCode);

  // Start the PID controller
  myPID.SetMode(AUTOMATIC);
  myPID.SetOutputLimits(-5000, 5000); // Output limits for the PID controller. These should be tuned for your specific system

    // Initialize the IMU
  if (!IMU.begin()) {
    Serial.println("Failed to initialize IMU!");
    while (1);
  }
}

void loop() {
  // Check if there are any UDP packets to read
  int packetSize = Udp.parsePacket();
  if (packetSize) {
    // Read the packet into the buffer
    Udp.read(packetBuffer, 255);
    // Null-terminate the string
    packetBuffer[packetSize] = 0;
    // Print the received message
    Serial.print("Received message: ");
    Serial.println(packetBuffer);
    // read and do the command
    command = String(packetBuffer);
    int commandStart = 0;
    int rst = parseCommand(command);
    // Send continue signal
    IPAddress remoteIp(ip1, ip2, ip3, ip4); // replace with your computer's IP address
    if (rst == 1){ // only send RSSI data on moving action
      Udp.beginPacket(remoteIp, remotePort);
      long rssi = WiFi.RSSI();
      int loop = 10;
      for(int i = 0; i < loop-1; i++){
        delay(1000);
        rssi += WiFi.RSSI();
      }
      rssi = rssi/loop;
      Udp.write(String(rssi).c_str());
      Udp.endPacket();
      Serial.println("RSSI signal sent!");
      delay(500);
    }

    Udp.beginPacket(remoteIp, remotePort);
    Udp.write(StartCode);
    Udp.endPacket();
    Serial.println("next signal sent!");
  }
  // delay(5000); // wait 5 seconds before sending the next message
  // moveForward(8000);
}

int parseCommand(String command) {
  // Get the action (first character of the command)
  char action = command.charAt(0);

  // Get the value (rest of the command)
  int value = command.substring(1).toInt();

  switch (action) {
    case 'F':
      moveForward(value);
      return 1;
      break;
    case 'B':
      moveBackward(value);
      return 1;
      break;
    case 'L':
      turnLeft(value);
      return 2;
      break;
    case 'R':
      turnRight(value);
      return 2;
      break;
    case 'S':
      stopMotors();
      break;
    case 'l':
      if(value >= 0){
        l_stop_time = value;
      } 
      break;
    case 'r':
      if(value >= 0){
        r_stop_time = value;
      } 
      break;
    default:
      Serial.println("Unknown command.");
      break;
  }
  return 0;
}
unsigned long timeOn;
unsigned long timeOff;
unsigned long index;
void moveForward(int seconds) {
  // set the starting heading direction as init
  Setpoint = 0;
  timeOn = millis();
  timeOff = timeOn;
  index = 0;
  while(timeOff - timeOn < seconds){
    // PID adjust
    Input = getHeadingFromIMU();
    myPID.Compute();
    l_stop_time = BASE_L_STOP_TIME + Output;
    r_stop_time = BASE_R_STOP_TIME - Output;
    l_stop_time = constrain(l_stop_time, MIN_STOP_TIME, MAX_STOP_TIME);
    r_stop_time = constrain(r_stop_time, MIN_STOP_TIME, MAX_STOP_TIME);
    Serial.print("Adjustment is ");
    Serial.print(Output);
    Serial.print(" the stop times are ");
    Serial.print(l_stop_time);
    Serial.print(" - ");
    Serial.println(r_stop_time);
    digitalWrite(directionPinL, LOW);
    digitalWrite(directionPinR, LOW);
    if(l_stop_time != 0 && index % l_stop_time == 0){
      analogWrite(pwmPinL, 0);
    } else {
      analogWrite(pwmPinL, speed);
    }
    if(r_stop_time != 0 && index % r_stop_time == 0){
      analogWrite(pwmPinR, 0);
    } else {
      analogWrite(pwmPinR, speed);
    }
    digitalWrite(brakePinL, LOW);
    digitalWrite(brakePinR, LOW);
    timeOff = millis();
    index = index + 1;
  }
  l_stop_time = BASE_L_STOP_TIME;
  r_stop_time = BASE_R_STOP_TIME;

  // delay(seconds);

  stopMotors();
}

void moveBackward(int seconds) {
  // set the starting heading direction as init
  Setpoint = 0;
  timeOn = millis();
  timeOff = timeOn;
  index = 0;
  while(timeOff - timeOn < seconds){
    // PID adjust
    Input = getHeadingFromIMU();
    myPID.Compute();
    l_stop_time = BASE_L_STOP_TIME + Output;
    r_stop_time = BASE_R_STOP_TIME - Output;
    l_stop_time = constrain(l_stop_time, MIN_STOP_TIME, MAX_STOP_TIME);
    r_stop_time = constrain(r_stop_time, MIN_STOP_TIME, MAX_STOP_TIME);
    digitalWrite(directionPinL, HIGH);
    digitalWrite(directionPinR, HIGH);
    if(l_stop_time != 0 && index % l_stop_time == 0){
      analogWrite(pwmPinL, 0);
    } else {
      analogWrite(pwmPinL, speed);
    }
    if(r_stop_time != 0 && index % r_stop_time == 0){
      analogWrite(pwmPinR, 0);
    } else {
      analogWrite(pwmPinR, speed);
    }
    digitalWrite(brakePinL, LOW);
    digitalWrite(brakePinR, LOW);
    timeOff = millis();
    index = index + 1;
  }
  l_stop_time = BASE_L_STOP_TIME;
  r_stop_time = BASE_R_STOP_TIME;
  stopMotors();
}

void turnLeft(int ms) {
  l_stop_time = BASE_L_STOP_TIME;
  r_stop_time = BASE_R_STOP_TIME;
  timeOn = millis();
  timeOff = timeOn;
  while(timeOff - timeOn < ms){
    digitalWrite(directionPinR, LOW);
    digitalWrite(directionPinL, HIGH);
    analogWrite(pwmPinL, speed);
    analogWrite(pwmPinR, speed);
    digitalWrite(brakePinL, LOW);
    digitalWrite(brakePinR, LOW);
    timeOff = millis();
  }
  stopMotors();
}

void turnRight(int ms) {
  l_stop_time = BASE_L_STOP_TIME;
  r_stop_time = BASE_R_STOP_TIME;
  timeOn = millis();
  timeOff = timeOn;
  while(timeOff - timeOn < ms){
    digitalWrite(directionPinR, HIGH);
    digitalWrite(directionPinL, LOW);
    analogWrite(pwmPinL, speed);
    analogWrite(pwmPinR, speed);
    digitalWrite(brakePinL, LOW);
    digitalWrite(brakePinR, LOW);
    timeOff = millis();
  }
  stopMotors();
}

void stopMotors() {
  digitalWrite(brakePinL, HIGH);
  digitalWrite(brakePinR, HIGH);

  // In case inertia effects
  delay(1000);
}

float getHeadingFromIMU() {
  float x, y, z;
  
  if (IMU.accelerationAvailable()) {
    IMU.readAcceleration(x, y, z);
  }
  
  // // Convert acceleration values to angles
  // float pitch = atan2(y, sqrt(pow(x, 2) + pow(z, 2))) * 180.0 / PI;
  // float roll = atan2(-x, sqrt(pow(y, 2) + pow(z, 2))) * 180.0 / PI;

  // Use pitch and roll to compute heading
  
  // // Placeholder: replace this with actual heading calculation
  // float heading = someFunctionOf(pitch, roll);

  return y;
}
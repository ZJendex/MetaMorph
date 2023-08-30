#include <SPI.h>
#include <WiFiNINA.h>
#include <WiFiUdp.h>
#include <Arduino_LSM6DS3.h> // IMU
#include <PID_v1.h> // PID control

// To do, flash with correct id
String rx = "2";

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
char EndCode[] = "bye"; 
long int startTime = 0;
long int endTime = 0;

String command = "";
void setup() {
  // Initialize serial and wait for port to open:
  Serial.begin(9600);

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
  String message =  rx + " " + StartCode;
  Udp.write(message.c_str());
  Udp.endPacket();
  Serial.print("Sent: ");
  Serial.println(message);
}

int recording = -1;
long RSSI_data_cnt = 0;
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
    if(strcmp(command.c_str(),"start") == 0){
      recording = 1;
      startTime = millis();
    }
    if(strcmp(command.c_str(),"end") == 0){
      recording = 0;
    }
    Serial.println("recording now is ");
    Serial.println(recording);
  }
  IPAddress remoteIp(ip1, ip2, ip3, ip4); // replace with your computer's IP address
  if(recording == 1){
    Udp.beginPacket(remoteIp, remotePort);
    long rssi = WiFi.RSSI();
    String message =  rx + " " + String(rssi);
    Udp.write(message.c_str());
    Udp.endPacket();
    RSSI_data_cnt += 1;
  }
  if(RSSI_data_cnt >= 5000){
    recording = 0;
  }
  if(recording == 0){
    endTime = millis();
    // send the total data length
    Udp.beginPacket(remoteIp, remotePort);
    String message =  rx + " " + String(RSSI_data_cnt);
    Udp.write(message.c_str());
    Udp.endPacket();
    int long totalTime = endTime - startTime;
    // send the duration
    Udp.beginPacket(remoteIp, remotePort);
    message =  rx + " " + String(totalTime);
    Udp.write(message.c_str());
    Udp.endPacket();
    // send finish signal
    Udp.beginPacket(remoteIp, remotePort);
    Udp.write(EndCode);
    Udp.endPacket();
    recording = -1;
    RSSI_data_cnt = 0;
  }
  delay(10);
}


import socket
import readline
import time
import struct
from datetime import datetime
import serial
from time import sleep

'''
Comunication to patch control system
'''
# 0:BLOW 1:HOLD 2:RELEASE
dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
print("Establishing connection...")
sleep(2)

# dev.write(b'0')
# print(dev.readline())
# sleep(12)
# dev.write(b'1')
# print(dev.readline())
# sleep(6)
# dev.write(b'2')
# print(dev.readline())
# sleep(6)
# dev.write(b'3')
# print(dev.readline())


'''
Communication to wifi board
'''
# Set up a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Replace with your desired host and port
# Host ip address on MAC >ipconfig getifaddr en0
# port should be set as same as you set in arduino code
host = '192.168.1.150'
port = 2391
startCode = "hi"
endCode = "bye"

# Bind the socket to the address
sock.bind((host, port))

print("Wait for the start code...")
# To get the addr from sender(the arduino ip address)
# the arduino should send the message first
data, addr = sock.recvfrom(1024)
while data.decode() != startCode:
    continue



'''
Running logic
'''
# start get RSSI data
user_inputs = "start"
print(f'Sending message: {user_inputs} to {addr}')
sock.sendto(user_inputs.encode(), addr)
while True: 
    data = bytes(4)
    data, addr = sock.recvfrom(1024)
    if len(data) != 0:
        rd = data.decode()  # Decode bytes to string
        if rd != endCode and rd != startCode:
            rssi = int(rd)  # Convert string to integer
            print('Current RSSI:', rssi)
    with open("target_RSSI", "r") as file:
        target = int(file.readline().strip())
        print("Target RSSI:", target)
    threshold = 2
    if rssi + 2 < target:
        dev.write(b'2') # release patch
        print(dev.readline())
    elif rssi - 2 > target:
        dev.write(b'0') # release patch
        print(dev.readline())
    else:
        dev.write(b'1') # hold patch
        print(dev.readline())
    sleep(1) # frequency
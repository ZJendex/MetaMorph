import socket
import readline
import time
import struct
from time import sleep

from datetime import datetime

'''
input record to get RSSI median value through time
'''

'''
default sataus 22 -> 35db
10 -> lower 3db
01 -> plus 5db
00 -> plus 3db

'''


# Connect the Arduino and local computer in the same wifi connection
# run the code first then run arduino

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

while True:
    sleep(2)
    user_inputs = "record"

    print(f'Sending message: {user_inputs} to {addr}')
    sock.sendto(user_inputs.encode(), addr)
    data = bytes(4)
    while data.decode() != endCode:        
            data, addr = sock.recvfrom(1024)
            if len(data) != 0:
                rd = data.decode()  # Decode bytes to string
                print(rd.split()[0] + ": " + rd.split()[1])
                user_inputs = "received"
                print(f'Sending message: {user_inputs} to {addr}')
                sock.sendto(user_inputs.encode(), addr)
                break
                # if rd != endCode and rd != startCode:
                #     rssi = int(rd)  # Convert string to integer
                #     print('RSSI:', rssi)
                #     with open('../data/rssi_data_car_bending.txt', 'a') as file:
                #         file.write(str(rssi))
                #         file.write("\n")
    
    
    





import socket
import readline
import time
import struct

from datetime import datetime


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
    user_inputs = input("Please enter a command: ") # command: start

    print(f'Sending message: {user_inputs} to {addr}')
    sock.sendto(user_inputs.encode(), addr)
    data = bytes(4)
    while data.decode() != endCode:        
            data, addr = sock.recvfrom(1024)
            if len(data) != 0:
                rd = data.decode()  # Decode bytes to string
                if rd != endCode and rd != startCode:
                    rssi = int(rd)  # Convert string to integer
                    print('RSSI:', rssi)
                    with open('../data/rssi_data_car_bending.txt', 'a') as file:
                        file.write(str(rssi))
                        file.write("\n")
    
    
    





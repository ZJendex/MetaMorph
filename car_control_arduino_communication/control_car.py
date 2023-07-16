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


# Bind the socket to the address
sock.bind((host, port))

print("Wait for the start code...")
# To get the addr from sender(the arduino ip address)
# the arduino should send the message first
data, addr = sock.recvfrom(1024)
while data.decode() != startCode:
    continue

while True:
    user_inputs = input("Please enter a command: ")
    # # Receive a message (up to 1024 bytes)
    # data, addr = sock.recvfrom(1024)

    # # Print the received message
    # print(f'Received message: {data.decode()} from {addr}')

    # Send a response
    # response = 'acknowledged'

    print(f'Sending message: {user_inputs} to {addr}')
    for user_input in user_inputs.split():
        sock.sendto(user_input.encode(), addr)
        print(f'Sending message: {user_input} to {addr}')
        data = bytes(4)
        print("Wait for the work done signal...")
        while data.decode() != startCode:        
            data, addr = sock.recvfrom(1024)
            if len(data) != 0:
                rd = data.decode()  # Decode bytes to string
                if rd != startCode:
                    rssi = int(rd)  # Convert string to integer
                    print('RSSI:', rssi)
                    with open('../data/rssi_data_car.txt', 'a') as file:
                        file.write(str(rssi))
                        file.write("\n")

#23 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 L500 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200
#14 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200 F2200
#13 F2200 F2200 F2200 F2200 F2200 L600 F2200 F2200 F2200 R600 F2200 F2200 F2200 F2200 F2200 
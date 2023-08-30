import socket
import readline
import time
import struct

from datetime import datetime

'''
01 blow
21 release
11 hold
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
device = 0
addr1 = -1
addr2 = -1
# To get the addr from sender(the arduino ip address)
# the arduino should send the message first
while True:
    data, addr = sock.recvfrom(1024)
    message = data.decode()
    print("get message: ")
    print(message)
    if message.split()[0] == "1" and message.split()[1] == startCode:
        addr1 = addr
        device += 1
        print(f"get deivce with addr {addr1}")
    if message.split()[0] == "2" and message.split()[1] == startCode:
        addr2 = addr
        device += 1
        print(f"get deivce with addr {addr2}")
    if device == 2:
        break

while True:
    end_signal_num = 0
    user_inputs = input("Please enter a command: ") # command: start
    print(f'Sending message: {user_inputs} to {addr1} and addr2 {addr2}')
    sock.sendto(user_inputs.encode(), addr1)
    sock.sendto(user_inputs.encode(), addr2)
    data = bytes(4)
    while True:
        if data.decode() == endCode:
            end_signal_num += 1
        if end_signal_num == 2:
            break
        data, addr = sock.recvfrom(1024)
        if len(data) != 0:
            rd = data.decode()  # Decode bytes to string
            if rd.split()[0] == "1":
                rssi = int(rd.split()[1])  # Convert string to integer
                print('RSSI At loc 1:', rssi)
                with open('../data/rssi_data_car_bending_loc1.txt', 'a') as file:
                    file.write(str(rssi))
                    file.write("\n")
            if rd.split()[0] == "2":
                rssi = int(rd.split()[1])  # Convert string to integer
                print('RSSI At loc 2:', rssi)
                with open('../data/rssi_data_car_bending_loc2.txt', 'a') as file:
                    file.write(str(rssi))
                    file.write("\n")
    
    
    





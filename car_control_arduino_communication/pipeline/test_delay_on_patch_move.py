import socket
import readline
import time
import struct
from datetime import datetime
import serial
from time import sleep
import time
import pipline_methods as pm
import gym
from collections import deque, Counter
from gym import spaces
import numpy as np
import statistics
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import signal
import pipline_RL_env_agent as rl
import matplotlib.pyplot as plt
BLOW = 0
HOLD = 1
RELEASE = 2

'''
Communication to serial port
'''
dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
print("Establishing connection...")
sleep(0.5)

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

flag = False
sock.settimeout(2)
while True:
    if flag:
        print("recovery patch")
        pm.serial_send(dev, "RELEASE")
        sleep(5)
        pm.serial_send(dev, "HOLD")
    flag = True
    input("enter to start...")
    print("Start Blow!!")
    pm.serial_send(dev, "BLOW")
    user_inputs = "start"
    sock.sendto(user_inputs.encode(), addr)
    data = bytes(4)
    while data.decode() != endCode:        
            try:
                data, addr = sock.recvfrom(1024)
            except socket.timeout:
                print("recovery patch")
                pm.serial_send(dev, "RELEASE")
                sleep(5)
                pm.serial_send(dev, "HOLD")
                continue
            if len(data) != 0:
                rd = data.decode()  # Decode bytes to string
                if rd != endCode and rd != startCode:
                    rssi = int(rd)  # Convert string to integer
                    with open('../../data/rssi_data_delay_test.txt', 'a') as file:
                        file.write(str(rssi))
                        file.write("\n")


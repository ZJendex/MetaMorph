import socket
import readline
import time
import struct
from datetime import datetime
import serial
from time import sleep
import time
import pipline_methods_linear as pm
import gym
from collections import deque, Counter
from gym import spaces
import numpy as np
import statistics
import signal
import matplotlib.pyplot as plt
import math
import pickle

# Define the action = (action1, action2)
BLOW = 0
HOLD = 1
RELEASE = 2
BLOW2 = 0
HOLD2 = 1
RELEASE2 = 2

# test length
tl = 5

data_id_buff = ""

'''
Comunication to patch control system
'''
# 0:BLOW 1:HOLD 2:RELEASE
# dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
dev = serial.Serial("/dev/cu.usbmodem1101", baudrate=9600)

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

# start get RSSI data
user_inputs = "start"
print(f'Sending message: {user_inputs} to {addr}')
sock.sendto(user_inputs.encode(), addr)

test_start = time.time()
rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
patch1TraverseActionSequence = [(BLOW, HOLD2)] * tl
patch2TraverseActionSequence = [(HOLD, BLOW2)] * tl
patch1ResetActionSequence = [(RELEASE, HOLD2)] * tl
patch2ResetActionSequence = [(HOLD, RELEASE2)] * tl
patchResetActionSequence = [(RELEASE, RELEASE2)] * tl
actionHold = (HOLD, HOLD2)

def patchOpt(patchNum, mode):
    global data_id_buff
    print(f"Optimizaing patch {patchNum}")
    if mode == 1: # h
        tmp_rssi = -1000
    elif mode == 2: # l 
        tmp_rssi = 1000
    else:
        input("Please input the correct mode")
        exit(0)
    
    if patchNum == 1:
        traverseActionSeq = patch1TraverseActionSequence
    elif patchNum == 2:
        traverseActionSeq = patch2TraverseActionSequence
    else:
        input("Please input the correct patch index")
        exit(0)

    if patchNum == 1:
        resetActionSeq = patch1ResetActionSequence
    elif patchNum == 2:
        resetActionSeq = patch2ResetActionSequence
    else:
        input("Please input the correct patch index")
        exit(0)

    # search
    tmp_index = 0
    index = 0
    for action in traverseActionSeq:
        # rssi is the consequence of the pre action
        rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
        print(f"current rssi is {rssi}")
        pm.serial_send_syn(dev, action)
        if mode == 1: # h
            if tmp_rssi < rssi:
                tmp_rssi = rssi
                tmp_index = index   
        if mode == 2: # l 
            if tmp_rssi > rssi:
                tmp_rssi = rssi
                tmp_index = index   
        index += 1
    pm.serial_send_syn(dev, actionHold)
    print(f"Get the best rssi at {tmp_rssi} with index {tmp_index}")
    sleep(1)
    print("Resetting...")
    # reset
    for action in resetActionSeq:
        pm.serial_send_syn(dev, action)
    pm.serial_send_syn(dev, actionHold)
    print("Reset Done")
    sleep(1)
    print("Go the the best place")
    index = 0
    for action in traverseActionSeq:
        print(f"index is {index} where the target index is {tmp_index}")
        pm.serial_send_syn(dev, action)
        if index == tmp_index:
            pm.serial_send_syn(dev, actionHold)
            break
        index += 1
    print(f"Patch {patchNum} optimize done")
    # rssi is the consequence of the pre action
    rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
    print(f"final rssi is {rssi}, the target rssi is {tmp_rssi}")

while True:
    # Read user input
    user_input = input("Enter 'h' for mode 1 or 'l' for mode 2: ")

    # Check the input and change the mode accordingly
    if user_input == 'h':
        mode = 1
    elif user_input == 'l':
        mode = 2
    else:
        print("Invalid input. Please enter 'h' or 'l'.")
        continue
    
    i = 0
    while True:
        if i % 1 == 0:
            command = input("Enter return for next around or q to back to mode selection: ")
            if command == 'q':
                break
        patchOpt(1, mode)
        # patchOpt(2, mode)
        i += 1
        




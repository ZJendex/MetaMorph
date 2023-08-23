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

data_id_buff = ""

'''
Comunication to patch control system
'''
# 0:BLOW 1:HOLD 2:RELEASE
# dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
dev = serial.Serial("/dev/cu.usbmodem11301", baudrate=9600)

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
patch1TraverseActionSequence = [(BLOW, HOLD2) * 10]
patch2TraverseActionSequence = [(HOLD, BLOW2) * 10]
patch1ResetActionSequence = [(RELEASE, HOLD2) * 10]
patch2ResetActionSequence = [(HOLD, RELEASE2) * 10]
patchResetActionSequence = [(RELEASE, RELEASE2) * 10]
actionHold = (HOLD, HOLD2)

def patchOpt(patchNum, mode):
    print(f"Optimizaing patch {patchNum}")
    if mode == 1: # h
        tmp_rssi = -1000
    if mode == 2: # l 
        tmp_rssi = 1000
    else:
        input("Please input the correct mode")
        exit(0)
    
    tmp_index = 0
    index = 0
    if patchNum == 1:
        traverseActionSeq = patch1TraverseActionSequence
    if patchNum == 2:
        traverseActionSeq = patch2TraverseActionSequence
    else:
        input("Please input the correct patch index")
        exit(0)

    if patchNum == 1:
        resetActionSeq = patch1ResetActionSequence
    if patchNum == 2:
        resetActionSeq = patch2ResetActionSequence
    else:
        input("Please input the correct patch index")
        exit(0)
    # search
    for action in traverseActionSeq:
        # rssi is the consequence of the pre action
        rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
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
    print(f"Get the best rssi at {rssi} with index {index}")

    print("Resetting...")
    # reset
    for action in resetActionSeq:
        # rssi is the consequence of the pre action
        rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
        pm.serial_send_syn(dev, action)
    print("Reset Done")

    print("Go the the best place")
    index = 0
    for action in traverseActionSeq:
        pm.serial_send_syn(dev, action)
        if index == tmp_index:
            break
    print(f"Patch {patchNum} optimize done")
while True:
    input_message = input("Input h or l to config the goal of the system: ")
    if input_message == "h":
        mode = 1
    if input_message == "l":
        mode = 2
    else:
        print("please input the correst config")
        continue
    
    i = 0
    while True:
        if i % 3 == 0:
            input("Enter return for next around")
        patchOpt(1, mode)
        patchOpt(2, mode)
        i += 1
        




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

rssi_history = []
def signal_handler(sig, frame):
    global rssi_history
    total_time = abs(init_time - time.time())
    print(f"the total time is {total_time}s")
    print(f"rssi history is {rssi_history} in length {len(rssi_history)}")
    rssi_history = np.array(rssi_history)
    np.savetxt(f"../data_pipeline/rssi_history_{total_time}.npy", rssi_history)
    
    # Exit the program gracefully
    exit(0)

# Set the signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)


# Define the action = (action1, action2)
BLOW = 0
HOLD = 1
RELEASE = 2
BLOW2 = 0
HOLD2 = 1
RELEASE2 = 2

# test length
tl = 4

data_id_buff = ""

'''
Comunication to patch control system
'''
# 0:BLOW 1:HOLD 2:RELEASE
# dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
dev = serial.Serial("/dev/cu.usbmodem1101", baudrate=9600)
dev2 = serial.Serial("/dev/cu.usbmodem1301", baudrate=9600)
dev3 = serial.Serial("/dev/cu.usbmodem1203", baudrate=115200)

print("Establishing connection...")
sleep(0.5)



test_start = time.time()
rssi, data_id_buff = pm.get_rssi_from_lora_board(dev3)
patch1TraverseActionSequence = [(BLOW, HOLD2)] * tl
patch2TraverseActionSequence = [(HOLD, BLOW2)] * tl
patch1ResetActionSequence = [(RELEASE, HOLD2)] * (tl-1)
patch2ResetActionSequence = [(HOLD, RELEASE2)] * (tl-1)
patchResetActionSequence = [(RELEASE, RELEASE2)] * (tl-1)
actionHold = (HOLD, HOLD2)
rssi_history = []

def patchOpt(patchNum, mode, dev):
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
        rssi, data_id_buff = pm.get_rssi_from_lora_board(dev3)
        rssi_history.append(rssi)
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
    # pm.serial_send_syn(dev, actionHold)
    print(f"Get the best rssi at {tmp_rssi} with index {tmp_index}")
    # sleep(1)
    print("Resetting...")
    # reset
    for action in resetActionSeq:
        rssi, data_id_buff = pm.get_rssi_from_lora_board(dev3)
        rssi_history.append(rssi)
        pm.serial_send_syn(dev, action)
        
    # pm.serial_send_syn(dev, actionHold)
    print("Reset Done")
    # sleep(1)
    print("Go the the best place")
    index = 0
    for action in traverseActionSeq:
        print(f"index is {index} where the target index is {tmp_index}")
        rssi, data_id_buff = pm.get_rssi_from_lora_board(dev3)
        rssi_history.append(rssi)
        pm.serial_send_syn(dev, action)
        if index == tmp_index:
            rssi, data_id_buff = pm.get_rssi_from_lora_board(dev3)
            rssi_history.append(rssi)
            pm.serial_send_syn(dev, actionHold)
            break
        index += 1
    print(f"Patch {patchNum} optimize done")
    # rssi is the consequence of the pre action
    rssi, data_id_buff = pm.get_rssi_from_lora_board(dev3)
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
    start_time = time.time()
    init_time = start_time
    total_time = 0
    rssi_pre = 0
    rssi_seq = []
    while True:
        print(f"i is {i}")
        if i != 0:
            rssi, data_id_buff = pm.get_rssi_from_lora_board(dev3)
            rssi_history.append(rssi)
            print(f"INIT rssi is {rssi}")
            sleep(1)     
            continue   
            # command = input("Enter return for next around or q to back to mode selection: ")
            # if command == 'q':
            #     break
        # if i % 1 == 0 and i != 0:
        #     command = input("Enter return for next around or q to back to mode selection or t to get a sequence of rssi data: ")
        #     if command == 'q':
        #         break
        #     if command == 't':
        #         rssi_seq = []
        #         for i in range(30):
        #             rssi, data_id_buff = pm.get_rssi_from_lora_board(dev3)
        #             rssi_seq.append(rssi)
        #         print(rssi_seq)
        
        start_time = time.time()
        rssi, data_id_buff = pm.get_rssi_from_lora_board(dev3)
        print(f"current rssi is {rssi}")
        patchOpt(1, mode, dev)
        patchOpt(2, mode, dev)
        patchOpt(1, mode, dev2)
        patchOpt(2, mode, dev2)
        print(f"delay time is {time.time() -  start_time}")
        i = 1



        




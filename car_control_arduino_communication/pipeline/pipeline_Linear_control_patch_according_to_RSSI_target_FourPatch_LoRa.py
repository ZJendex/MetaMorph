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

rssi_history = []
def signal_handler(sig, frame):
    global rssi_history
    total_time = abs(start_time - time.time())
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
tl = 5

data_id_buff = ""

'''
Comunication to patch control system
'''
# 0:BLOW 1:HOLD 2:RELEASE
# dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
dev1 = serial.Serial("/dev/cu.usbmodem1101", baudrate=9600)
dev2 = serial.Serial("/dev/cu.usbmodem1301", baudrate=9600)

print("Establishing connection...")
sleep(0.5)


patch1TraverseActionSequence = [(BLOW, HOLD2)] * tl
patch2TraverseActionSequence = [(HOLD, BLOW2)] * tl
patch1ResetActionSequence = [(RELEASE, HOLD2)] * tl
patch2ResetActionSequence = [(HOLD, RELEASE2)] * tl
patchResetActionSequence = [(RELEASE, RELEASE2)] * tl
actionHold = (HOLD, HOLD2)
rssi_history = []
dev = dev1
while True:
    # Read user input
    rssi = input("rssi value from LoRa is: ")
    rssi = int(rssi)
    devInput = input("dev 1 for low and 2 for high: ")
    if devInput == '1':
        dev = dev1
    elif devInput == '2':
        dev = dev2
    
    actionInput = input("actions: ")
    action1 = int(actionInput[0])
    aciton2 = int(actionInput[1])

    pm.serial_send_syn(dev, (action1, aciton2))
    sleep(2)
    pm.serial_send_syn(dev, (HOLD, HOLD2))


    
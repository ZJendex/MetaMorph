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
BLOW2 = 0
HOLD2 = 1
RELEASE2 = 2

# dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
dev = serial.Serial("/dev/cu.usbmodem11301", baudrate=9600)
print("Establishing connection...")
sleep(0.5)

# # test the serial send
# while True:
#     command = input("Please input 0 1 2 to control the patch:")
#     if command == "0":
#         pm.serial_send(dev, "BLOW")
#     if command == "1":
#         pm.serial_send(dev, "HOLD")
#     if command == "2":
#         pm.serial_send(dev, "RELEASE")
    
#     if command == "3":
#         pm.serial_send(dev, "BLOW2")
#     if command == "4":
#         pm.serial_send(dev, "HOLD2")
#     if command == "5":
#         pm.serial_send(dev, "RELEASE2")

# test serial send syn
'''
message
action(Action1, Action2)
Action1: 0, 1, 2 where 0 is blow, 1 is hold, 2 is release
Action2: 0, 1, 2 where 0 is blow, 1 is hold, 2 is release
'''
while True:
    command = input("Please input [0,1,2][0,1,2] to control the patch:")
    action = (int(command[0]), int(command[1]))
    pm.serial_send_syn(dev, action)
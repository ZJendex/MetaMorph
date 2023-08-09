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

dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
print("Establishing connection...")
sleep(0.5)

while True:
    command = input("Please input 0 1 2 to control the patch:")
    if command == "0":
        pm.serial_send(dev, "BLOW")
    elif command == "1":
        pm.serial_send(dev, "HOLD")
    elif command == "2":
        pm.serial_send(dev, "RELEASE")
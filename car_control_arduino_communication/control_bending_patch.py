import socket
import readline
import time
import struct
from datetime import datetime
import serial
from time import sleep

# 0:BLOW 1:HOLD 2:RELEASE
dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
print("Establishing connection...")
sleep(2)
dev.write(b'0')
print(dev.readline())
sleep(12)
dev.write(b'1')
print(dev.readline())
sleep(6)
dev.write(b'2')
print(dev.readline())
sleep(6)
dev.write(b'3')
print(dev.readline())



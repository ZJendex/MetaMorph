import socket
import readline
import time
import struct
from datetime import datetime
import serial
from time import sleep
import time

'''
Comunication to patch control system
'''
# 0:BLOW 1:HOLD 2:RELEASE
dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
print("Establishing connection...")
sleep(0.5)

# dev.write(b'0')
# print(dev.readline())
# sleep(12)
# dev.write(b'1')
# print(dev.readline())
# sleep(6)
# dev.write(b'2')
# print(dev.readline())
# sleep(6)
# dev.write(b'3')
# print(dev.readline())


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



'''
Running logic
'''
# start get RSSI data
user_inputs = "start"
print(f'Sending message: {user_inputs} to {addr}')
sock.sendto(user_inputs.encode(), addr)
test = 1
tHighest = -100
tLowest = 100
test_blow_flag = 0
data_id_buff = ""
input_message = input("Enter anything to start the test or enter NO to start without test: ")
if input_message == "NO":
    test = 0
test_start = time.time()
while True: 
    # Determine the mode
    if test == 1 and time.time() - test_start > 20: # 20 sec test for the range of patch operation
        sleep(1)
        test = 0
        dev.write(b'3') # stop patch
        with open("patch_ability_range", "w") as file:
            file.write(f"upper bound: {tHighest}\n")
            file.write(f"lower bound: {tLowest}\n")
        print("test finished")
        target = input("Please enter the target RSSI. (To be Notice, the further target change please change the file patch_target_RSSI directly. To do the re-test, please rewrite 999 in the file patch_target_RSSI): ")
        with open("patch_target_RSSI", "w") as file:
            file.write(target)
    # Get a RSSI avg Data from arduino wifi board
    user_inputs = "record"
    print(f'Sending message: {user_inputs} to {addr}')
    sock.sendto(user_inputs.encode(), addr)
    while True: # leave until received the RSSI avg Data
        data = bytes(1024)
        data, addr = sock.recvfrom(1024)
        if len(data) != 0:
            rd = data.decode()  # Decode bytes to string
            if rd.split()[0] == "RSSI": # header mached
                # for all received RSSI data, the data is only valid when the data_id is not the same as the previous one
                if rd.split()[2] != data_id_buff:
                    data_id_buff = rd.split()[2]
                    rssi = int(rd.split()[1])  # Convert string to integer
                    if test == 1:
                        print('Test RSSI:', rssi)
                    else:
                        print('Current RSSI:', rssi)
                    user_inputs = "received"
                    print(f'Sending message: {user_inputs} to {addr}')
                    sock.sendto(user_inputs.encode(), addr)
                    print(time.time())
                    break 
    # config for resend message
    resend_time = 4
    resent_cnt = 0
    # loop, test mode & operating mode
    if test == 1: # test mode
        if test_blow_flag == 0:
            dev.write(b'0') # blow patch
            while True: # ensure the device received the message
                if resent_cnt == resend_time:
                    dev.write(b'0')
                    resent_cnt = 0
                sleep(0.05)
                resent_cnt += 1
                rev_message = dev.readline().decode()
                if rev_message == "BLOW\n":
                    break
            test_blow_flag = 1
        if rssi > tHighest:
            tHighest = rssi
        if rssi < tLowest:
            tLowest = rssi
    else: # operating mode
        # Retrieve the target RSSI
        with open("patch_target_RSSI", "r") as file:
            target = int(file.readline().strip())
            if target == 999:
                test = 1
                test_start = time.time()
                tHighest = -100
                tLowest = 100
                test_blow_flag = 0
                continue
            print("Target RSSI:", target)


        # Decide how to respond
        threshold = 1
        if rssi + threshold < target:
            dev.write(b'2') # release patch
            while True: # ensure the device received the message
                if resent_cnt == resend_time:
                    dev.write(b'2')
                    resent_cnt = 0
                sleep(0.05)
                resent_cnt += 1
                rev_message = dev.readline().decode()
                if rev_message == "RELEASE\n":
                    break
            print(rev_message)
        elif rssi - threshold > target:
            dev.write(b'0') # blow patch
            while True: # ensure the device received the message
                if resent_cnt == resend_time:
                    dev.write(b'0')
                    resent_cnt = 0
                sleep(0.05)
                resent_cnt += 1
                rev_message = dev.readline().decode()
                if rev_message == "BLOW\n":
                    break
            print(rev_message)
        else:
            dev.write(b'1') # hold patch
            while True: # ensure the device received the message
                if resent_cnt == resend_time:
                    dev.write(b'1')
                    resent_cnt = 0
                sleep(0.05)
                resent_cnt += 1
                rev_message = dev.readline().decode()
                if rev_message == "HOLD\n":
                    break
            print(rev_message)
        sleep(1) # frequency





    '''
    When to stop the system?
    '''
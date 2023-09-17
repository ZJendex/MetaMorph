import socket
import time
import serial
from time import sleep
import time
import pipline_methods_linear as pm
from collections import deque
import numpy as np
import signal


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
tl = 8

data_id_buff = ""

'''
Comunication to patch control system
'''
# 0:BLOW 1:HOLD 2:RELEASE
# dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)

dev = serial.Serial("/dev/cu.usbmodem1101", baudrate=9600)
dev2 = serial.Serial("/dev/cu.usbmodem1301", baudrate=9600)

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
patch1ResetActionSequence = [(RELEASE, HOLD2)] * (tl-3)
patch2ResetActionSequence = [(HOLD, RELEASE2)] * (tl-3)
patchResetActionSequence = [(RELEASE, RELEASE2)] * 2
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
        rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
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
        rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
        rssi_history.append(rssi)
        pm.serial_send_syn(dev, action)
        
    # pm.serial_send_syn(dev, actionHold)
    print("Reset Done")
    # sleep(1)
    print("Go the the best place")
    index = 0
    for action in traverseActionSeq:
        print(f"index is {index} where the target index is {tmp_index}")
        rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
        rssi_history.append(rssi)
        if index == tmp_index:
            pm.serial_send_syn(dev, actionHold)
            break
        else:
            pm.serial_send_syn(dev, action)
            
        index += 1
    print(f"Patch {patchNum} optimize done")
    # rssi is the consequence of the pre action
    # rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
    print(f"final rssi is {rssi}, the target rssi is {tmp_rssi}")

while True:
    # Read user input
    # user_input = input("Enter 'h' for mode 1 or 'l' for mode 2: ")
    user_input = 'h'

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
    rssi_pre = rssi
    rssi_hisque = deque(maxlen=5)
    while True:
        if i != 0:
            rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
            rssi_history.append(rssi)
            print(f"INIT rssi is {rssi}")
            sleep(1)
            # if rssi - rssi_pre >= -5: # decrease above 5db

            if len(rssi_hisque) == 5 and (max(rssi_hisque) - min(rssi_hisque) > 5): # decrease above 5db
                print("new loop")
                rssi_hisque = deque(maxlen=5)
                # reset upper
                for action in patchResetActionSequence:
                    rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
                    rssi_history.append(rssi)
                    pm.serial_send_syn(dev2, action)
                    rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
                    rssi_history.append(rssi)
                    pm.serial_send_syn(dev, action)
                
                rssi_pre = rssi
                rssi_hisque.append(rssi_pre)
            else:
                print("nothing to do")
                rssi_pre = rssi
                rssi_hisque.append(rssi_pre)
                continue
                
            # command = input("Enter return for next around or q to back to mode selection: ")
            # if command == 'q':
            #     break
        
        start_time = time.time()
        rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
        print(f"current rssi is {rssi}")
        patchOpt(1, mode, dev)
        patchOpt(2, mode, dev)
        patchOpt(1, mode, dev2)
        patchOpt(2, mode, dev2)
        print(f"delay is {time.time() - start_time}s")
        i += 1



        




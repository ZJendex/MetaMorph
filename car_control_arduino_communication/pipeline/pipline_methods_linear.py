import socket
import readline
import time
import struct
from datetime import datetime
import serial
from time import sleep
import time

'''
message
action(Action1, Action2)
Action1: 0, 1, 2 where 0 is blow, 1 is hold, 2 is release
Action2: 0, 1, 2 where 0 is blow, 1 is hold, 2 is release
'''
previous_action = (-1, -1)
def serial_send_syn(dev, action):
    global previous_action
    if previous_action[0] == action[0] and previous_action[1] == action[1]:
        sleep(1)
        return
    else:
        previous_action = action
    action2serial = {
        (0, 0): b'14',
        (0, 1): b'16',
        (0, 2): b'15',
        (1, 0): b'74',
        (1, 1): b'76',
        (1, 2): b'75',
        (2, 0): b'24',
        (2, 1): b'26',
        (2, 2): b'25',
    }
    message_encode = action2serial[action]
    dev.write(message_encode) 
    action2str = {
        0: "BLOW",
        1: "HOLD",
        2: "RELEASE",
    }
    print(f"patch1 action is {action2str[action[0]]}")
    print(f"patch2 action is {action2str[action[1]]}")
    sleep(1)

# def get_rssi_from_usrp_via_serial(dev):
#     # To do
    

'''
message
BLOW   0
HOLD   1
RELEASE 2
'''
def serial_send(dev, message):
    if message == "BLOW":
        message_encode = b'4'
    elif message == "HOLD":
        message_encode = b'6'
    elif message == "RELEASE":
        message_encode = b'5'
    elif message == "STOP":
        message_encode = b'3'
    elif message == "HOLD2":
        message_encode = b'7'
    elif message == "RELEASE2":
        message_encode = b'2'
    elif message == "BLOW2":
        message_encode = b'1'

    # config for resend message
    resend_time = 4
    resent_cnt = 0
    dev.write(message_encode) 
    print(f"message is {message}")
    # print("making sure the arduino get the message {}", message)
    # while True: # ensure the device received the message
    #     if resent_cnt == resend_time:
    #         dev.write(message_encode) 
    #         resent_cnt = 0
    #     sleep(0.05)
    #     resent_cnt += 1
    #     rev_message = dev.readline().decode()
    #     if rev_message.startswith(message):
    #         break
    
    # return rev_message
    return "no receiving check"

def get_rssi_from_wifi_board(sock, addr, data_id_buff):
    sock.settimeout(1) # Set timeout to not let recvfrom blocking code
    user_inputs = "record"
    # print(f'Sending message: {user_inputs} to {addr}')
    
    sock.sendto(user_inputs.encode(), addr)
    sleep(0.2)
    while True: # leave until received the RSSI avg Data
        try:
            data, addr = sock.recvfrom(1024)
        except socket.timeout:
            print("timeout")
            print("resent the message")
            sock.sendto(user_inputs.encode(), addr)
            continue
        if len(data) != 0:
            rd = data.decode()  # Decode bytes to string
            if rd.split()[0] == "RSSI": # header mached
                # for all received RSSI data, the data is only valid when the data_id is not the same as the previous one
                if rd.split()[2] != data_id_buff:
                    data_id_buff = rd.split()[2]
                    rssi = float(rd.split()[1])  # Convert string to integer
                    user_inputs = "received"
                    # print(f'Sending message: {user_inputs} to {addr}')
                    sock.sendto(user_inputs.encode(), addr)
                    break 
    
    return rssi, data_id_buff

def get_rssi_from_lora_board(dev):
    start_time = time.time()
    total_rssi = 0
    num = 30
    # Flush input buffer, discarding all its contents
    dev.flushInput()
    data_received = dev.readline().decode('utf-8').strip()
    while (not data_received) or data_received.split()[0] != "TestRssi":
        data_received = dev.readline().decode('utf-8').strip()

    data_received = float(data_received.split()[1])
    total_rssi += data_received
    for _ in range(num-1):
        data_received = dev.readline().decode('utf-8').strip()
        data_received = float(data_received.split()[1])
        total_rssi += data_received
    
    avg_rssi = total_rssi/num
    print(f"Received LoRa avg rssi: {avg_rssi}")
    return avg_rssi, 0
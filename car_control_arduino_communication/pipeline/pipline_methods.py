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
    # config for resend message
    resend_time = 4
    resent_cnt = 0
    dev.write(message_encode) 
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
    sock.settimeout(5) # Set timeout to not let recvfrom blocking code
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
                    user_inputs = "received"
                    print(f'Sending message: {user_inputs} to {addr}')
                    sock.sendto(user_inputs.encode(), addr)
                    break 
    
    return rssi, data_id_buff
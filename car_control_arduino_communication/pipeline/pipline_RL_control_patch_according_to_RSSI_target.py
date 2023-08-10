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

def signal_handler(sig, frame):
    # This function will be called when the SIGINT signal is caught (Ctrl+C pressed)
    print("SIGINT signal caught. Performing cleanup...")
    # Perform the action you want to do when the signal is caught
    # For example, save data, close files, release resources, etc.
    # ...
    # # Plotting the loss
    # plt.figure(figsize=(10,5))
    # plt.plot(losses)
    # plt.title("Loss over Episodes")
    # plt.xlabel("Episode")
    # plt.ylabel("Loss")
    # plt.grid(True)
    # plt.show()

    # # Plotting the rewards (which is a proxy for accuracy/performance in RL)
    # plt.figure(figsize=(10,5))
    # plt.plot(total_rewards)
    # plt.title("Total Rewards over Episodes")
    # plt.xlabel("Episode")
    # plt.ylabel("Total Rewards")
    # plt.grid(True)
    # plt.show()
    fig, ax1 = plt.subplots(figsize=(10,5))

    color = 'tab:red'
    # Twin the axes
    ax2 = ax1.twinx()

    ax1.set_xlabel('Episode')
    ax1.set_ylabel('Loss', color=color)
    ax1.plot(losses, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    color = 'tab:blue'
    ax2.set_ylabel('Total Rewards', color=color)
    ax2.plot(total_rewards, color=color)
    ax2.tick_params(axis='y', labelcolor=color)

    plt.title("Loss and Total Rewards over Episodes")
    plt.grid(True)
    plt.savefig("RL_trainning_daily.png")
    # Exit the program gracefully
    exit(0)

# Set the signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)

'''
Comunication to patch control system
'''
# 0:BLOW 1:HOLD 2:RELEASE
dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
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


'''
Running logic
'''
# start get RSSI data
user_inputs = "start"
print(f'Sending message: {user_inputs} to {addr}')
sock.sendto(user_inputs.encode(), addr)
test = 1
pre_train = 1
pre_train_num = 20
pre_train_cur = 0
pre_train_action = rl.HOLD
tHighest = -100
tLowest = 100
test_blow_flag = 0
action = -1
pre_action = -1
data_id_buff = ""
input_message = input("Enter anything to start the strength test or enter N to start without strength test: ")
if input_message == "N":
    test = 0
if input_message == "NO":
    test = 0
    pre_train = 0
test_start = time.time()
rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
# Instantiate the environment and the agent
# Assume the Target RSSI never change
env = rl.MyEnvironment(target_value=-33, initial_value=rssi)
input_dim = env.max_length * 2
output_dim = env.num_actions  # Number of actions
agent = rl.PolicyGradientAgent(input_dim, output_dim)
done = False
state = env.reset()
episode = 0
total_rewards = []
losses = []
while True: 
    # Determine the mode
    if test == 1 and time.time() - test_start > 20: # 20 sec test for the range of patch operation
        sleep(1)
        test = 0
        # dev.write(b'3') # stop patch
        print("start sending the stop signal")
        pm.serial_send(dev, "STOP")
        
        with open("patch_ability_range", "w") as file:
            file.write(f"upper bound: {tHighest}\n")
            file.write(f"lower bound: {tLowest}\n")
        print("strength test finished")
        target = input("Please enter the target RSSI. (To be Notice, the further target change please change the file patch_target_RSSI directly. To do the re-test, please rewrite 999 in the file patch_target_RSSI): ")
        with open("patch_target_RSSI", "w") as file:
            file.write(target)
            env.target_value = int(target)
    # Get a RSSI avg Data from arduino wifi board
    rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
    if test == 1:
        print('Test RSSI:', rssi)
    else:
        print('Current RSSI:', rssi)
    
    # loop, test mode & operating mode
    if test == 1: # test mode
        if test_blow_flag == 0:
            rev_message = pm.serial_send(dev, "BLOW")
            test_blow_flag = 1
        if rssi > tHighest:
            tHighest = rssi
        if rssi < tLowest:
            tLowest = rssi
    elif pre_train == 1:
        if pre_train_cur < pre_train_num/2:
            rev_message = pm.serial_send(dev, "BLOW")
            env.step(pre_train_action, rssi)
            pre_train_action = rl.BLOW
        elif pre_train_cur < pre_train_num/2 + 3:
            rev_message = pm.serial_send(dev, "HOLD")
            env.step(pre_train_action, rssi)
            pre_train_action = rl.HOLD
        else:
            rev_message = pm.serial_send(dev, "RELEASE")
            env.step(pre_train_action, rssi)
            pre_train_action = rl.RELEASE

        pre_train_cur += 1
        if pre_train_cur == pre_train_num:
            pre_train = 0
            state = env.get_state()
            
    else: # operating mode + RL learning mode
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
            else:
                env.target_value = target
                if env.target_value != env.pre_target_value: # target changed, reset the environment
                    env.reset()
                    env.pre_target_value = env.target_value

            print("RL Target RSSI:", env.target_value)

        '''
        RL learning
        '''
        # new episode
        if done:
            total_reward, loss = agent.learn()
            # record the total reward and loss
            total_rewards.append(total_reward)
            losses.append(loss)
            # Print the results every 10 episodes
            if episode % 1 == 0: 
                with open('RL_trainning_daily', 'a') as file:
                    # Append lines to the file
                    file.write(f"Episode: {episode}, Total Reward: {total_reward}\n")
                
            # state = env.reset() # state need to fill with vaild 20 data to start the next episode
            done = False
            episode += 1

        if action != -1:
            # The action is performed and the new state, reward, and done flag are received
            next_state, reward, done, _ = env.step(action, rssi)
            # Save the reward got from env
            agent.record_rewards(reward)
            # The new state becomes the current state for the next iteration
            state = next_state

        # The agent chooses an action
        action = agent.get_action(state)

        # Move the patch
        if(action != pre_action):
            if action == rl.RELEASE:
                pm.serial_send(dev, "RELEASE")
            elif action == rl.BLOW:
                pm.serial_send(dev, "BLOW")
            else:
                pm.serial_send(dev, "HOLD")

            pre_action = action
        
        # print the action
        if action == 0:
            print("BLOW")
        if action == 1:
            print("HOLD")
        if action == 2:
            print("RELEASE")
        
    sleep(2) # frequency





    '''
    When to stop the system?
    '''
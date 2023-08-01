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


# Define the actions
BLOW = 0
HOLD = 1
RELEASE = 2



class MyEnvironment(gym.Env):
    def __init__(self, target_value, initial_value, max_length=20):
        super(MyEnvironment, self).__init__()

        self.action_space = spaces.Discrete(3)  # BLOW, HOLD, RELEASE
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(2, max_length))

        # Initial setup
        self.target_value = target_value
        self.current_value = initial_value
        self.prev_value = self.current_value
        # State Information
        # Temporary use action sequence and value sequence to represent the state
        # In the future, we can use the detailed floor plan image + air prerssure of each patch to represent the state
        self.action_sequence = deque([HOLD], maxlen=max_length)
        self.value_sequence = deque([self.current_value], maxlen=max_length)

    def step(self, action):
        # Update current value based on action
        # if action == BLOW:
        #     self.current_value += 1
        # elif action == HOLD:
        #     pass
        # elif action == RELEASE:
        self.current_value = rssi

        # Calculate the reward
        # reward = (self.target_value - self.prev_value) - (self.target_value - self.current_value)
        reward = abs(self.target_value - self.current_value)

        # Update action and value sequences
        self.action_sequence.append(action)
        self.value_sequence.append(self.current_value)

        # Check if the task is done
        # done = np.isclose(self.current_value, self.target_value, atol=0.01)
        # NEVER BE DONE ON LEARNING
        done = False

        self.prev_value = self.current_value

        # Format the State
        action_count_list = [(element, count) for element, count in Counter(self.action_sequence).items()]
        median_RSSI = statistics.median(self.value_sequence)

        return np.array([self.action_sequence, self.value_sequence]), reward, done, {}
        # return np.array([action_count_list, median_RSSI]), reward, done, {}

    def reset(self):
        self.current_value = self.prev_value
        self.action_sequence.clear()
        self.value_sequence.clear()
        self.action_sequence.append(HOLD)
        self.value_sequence.append(self.current_value)
        return np.array([self.action_sequence, self.value_sequence])

    def render(self, mode='human'):
        print(f'Target Value: {self.target_value}, Current Value: {self.current_value}, Actions: {list(self.action_sequence)}, Values: {list(self.value_sequence)}')

class QLearningAgent:
    def __init__(self, action_space, alpha=0.5, gamma=0.35, epsilon=0.7):
        self.action_space = action_space
        self.alpha = alpha # learning rate, the larger the alpha, the more the agent will consider the most recent information
        self.gamma = gamma # self.gamma is close to zero, the agent will tend to consider only immediate rewards
        self.epsilon = epsilon # exploration rate, the larger the epsilon, the more the agent will explore
        self.last_reward = 100
        self.last_target = 100

        # Assume that the state space size is known and is small enough for a tabular representation.
        # You'll have to replace this with a function approximator (e.g., a neural network) if not.
        self.Q = {}

    def get_action(self, state):
        state = str(state.tolist())  # Convert state to string to use as dictionary key

        # Initialize Q-values to 0 if state is new
        if state not in self.Q:
            self.Q[state] = np.zeros(self.action_space.n)

        # if the last reward is not too bad, then hold and decrease the curiosity
        if self.last_reward > -1 and self.last_reward < 1:
            self.epsilon = 0.3
            return HOLD
        self.epsilon = 0.7
        # Epsilon-greedy action selection
        if np.random.uniform(0, 1) < self.epsilon:
            return self.action_space.sample()  # Exploration
        else:
            return np.argmax(self.Q[state])  # Exploitation

    def learn(self, state, action, reward, next_state, done):
        self.last_reward = reward

        state = str(state.tolist())  # Convert state to string to use as dictionary key
        next_state = str(next_state.tolist())  # Convert next_state to string to use as dictionary key

        # Initialize Q-values to 0 if states are new
        if state not in self.Q:
            self.Q[state] = np.zeros(self.action_space.n)
        if next_state not in self.Q:
            self.Q[next_state] = np.zeros(self.action_space.n)

        # Q-Learning update
        target = reward + self.gamma * np.max(self.Q[next_state]) if not done else reward
        self.Q[state][action] = (1 - self.alpha) * self.Q[state][action] + self.alpha * target
   




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
tHighest = -100
tLowest = 100
test_blow_flag = 0
action = -1
pre_action = -1
data_id_buff = ""
input_message = input("Enter anything to start the strength test or enter NO to start without strength test: ")
if input_message == "NO":
    test = 0
test_start = time.time()
rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
# Instantiate the environment and the agent
# Assume the Target RSSI never change
env = MyEnvironment(target_value=-33, initial_value=rssi)
agent = QLearningAgent(env.action_space)
done = False
state = env.reset()
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
            # else:
            #     env.target_value = target
            #     if env.target_value != agent.last_target:
            #         env.reset()
            #         agent.last_target = env.target_value
            print("Target RSSI:", target)
            print("RL Target RSSI:", env.target_value)

        if action != -1:
            # The action is performed and the new state, reward, and done flag are received
            next_state, reward, done, _ = env.step(action)
            # The agent learns from the experience
            agent.learn(state, action, reward, next_state, done)
            # The new state becomes the current state for the next iteration
            state = next_state

        # The agent chooses an action
        action = agent.get_action(state)

        

        if(action != pre_action):
            if action == RELEASE:
                pm.serial_send(dev, "RELEASE")
            elif action == BLOW:
                pm.serial_send(dev, "BLOW")
            else:
                pm.serial_send(dev, "HOLD")

            pre_action = action
        
        if action == 0:
            print("BLOW")
        if action == 1:
            print("HOLD")
        if action == 2:
            print("RELEASE")
        
        sleep(1) # frequency





    '''
    When to stop the system?
    '''
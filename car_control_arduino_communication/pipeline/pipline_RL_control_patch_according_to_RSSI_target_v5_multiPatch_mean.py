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
import pipline_RL_env_agent as rl
import matplotlib.pyplot as plt
import math
import pickle
'''
on policy or off
model free or not 
cannot predict future
the future env is a black box
therefore q learning

delay, small amount of data 
therefore q learning

dqn absence greedy 
train inde signal strendgth data
'''

total_rewards = []
accuracy = []
RSSI_ALL = []
exploIR = []
exploi = -1
# Define the action = (action1, action2)
BLOW = 0
HOLD = 1
RELEASE = 2
BLOW2 = 0
HOLD2 = 1
RELEASE2 = 2
# Configuration
# Env
max_reward = 10
max_length = 2 # State sequence length
# Q learning
alpha=0.7 # learning rate, the larger the alpha, the more the agent will consider the most recent information
# future importance
gamma=0.75 # self.gamma is close to zero, the agent will tend to consider only immediate rewards
epsilon=0.7 # exploration rate, the larger the epsilon, the more the agent will explore

# goal config
goal = 0.5 # 1 for highest, -1 for lowest

# test full inflation
test = 0
tHighest = -100
tLowest = 100
test_blow_flag = 0
# fill state and change the target RSSI reasonable
pre_train = 1
pre_train_num = 20
pre_train_cur = 0
# enable dynamic target
dynamic_target = 1
target_try_cnt = 0
target_try_cnt_max = 20
RSSI_reset = []

# other init
action = (-1, -1)
pre_action = (-1, -1)
data_id_buff = ""

# rewards
beta = 1.2 # the closer to 1.1
al = 100 # the larger to 100

def signal_handler(sig, frame):
    global total_rewards, accuracy, RSSI_ALL, exploIR
    total_rewards = total_rewards[pre_train_num:]
    accuracy = accuracy[pre_train_num:]
    RSSI_ALL = RSSI_ALL[pre_train_num:]
    # This function will be called when the SIGINT signal is caught (Ctrl+C pressed)
    print("SIGINT signal caught. Performing cleanup...")
    fig, ax1 = plt.subplots(figsize=(14,10))
    color = 'tab:red'

    # First axis
    ax1.set_xlabel('steps')
    ax1.set_ylabel('rewards', color=color)
    ax1.plot(total_rewards, color=color)
    ax1.tick_params(axis='y', labelcolor=color)

    # Plotting the regression line for total_rewards
    x = np.arange(len(total_rewards))
    slope, intercept = np.polyfit(x, total_rewards, 1)
    regression_line = slope * x + intercept
    ax1.plot(x, regression_line, color='tab:red', linestyle='--')

    # Plotting the exploi effects
    color = 'tab:blue'
    ax1.plot(exploIR, color=color, label='exploi point')

    # conbine two axis together
    # Second axis
    ax2 = ax1.twinx()
    color = 'tab:blue'
    ax2.set_ylabel('Target RSSI', color=color)  # Updated label to reflect both datasets
    ax2.plot(accuracy, color=color, label='Target RSSI')
    ax2.tick_params(axis='y', labelcolor=color)

    # Plotting RSSI_ALL on the same axis as accuracy
    color = 'tab:green'
    ax2.plot(RSSI_ALL, color=color, label='RSSI')

    # Plotting the regression line for RSSI_ALL on ax2
    x = np.arange(len(RSSI_ALL))
    slope, intercept = np.polyfit(x, RSSI_ALL, 1)
    regression_line = slope * x + intercept
    ax2.plot(x, regression_line, color='tab:green', linestyle='--')  # Changed color to differentiate from RSSI_ALL

    # Optionally, add a legend to ax2 to differentiate the lines
    ax2.legend(loc='upper left')


    # # Adjust the position of the third axis to prevent overlap
    # ax3.spines['right'].set_position(('outward', 35))

    id = time.time()
    plt.title("Rewards, Target RSSI and RSSI Changes over Steps")
    plt.grid(True)

    plt.savefig(f"RL_trainning_daily_{id}.png")

    total_rewards = np.array(total_rewards)
    accuracy = np.array(accuracy)
    RSSI_ALL = np.array(RSSI_ALL)
    np.savetxt('data_training_reward_accuracy.txt', (total_rewards, accuracy, RSSI_ALL), fmt='%d')
    with open(f"data_qtable_{id}.pkl", "wb") as f:
        pickle.dump(agent.Q, f)
    # Exit the program gracefully
    exit(0)

# Set the signal handler for SIGINT
signal.signal(signal.SIGINT, signal_handler)

class MyEnvironment(gym.Env):
    def __init__(self, target_value, initial_value, max_length=max_length):
        super(MyEnvironment, self).__init__()

        self.action_space = spaces.Tuple((spaces.Discrete(3), spaces.Discrete(3)))  # BLOW, HOLD, RELEASE ; BLOW2, HOLD2, RELEASE2
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(2, max_length))

        # Initial setup
        self.target_value = target_value
        self.pre_target_value = target_value
        self.current_value = initial_value
        self.prev_value = self.current_value
        # State Information
        # Temporary use action sequence and value sequence to represent the state
        # In the future, we can use the detailed floor plan image + air prerssure of each patch to represent the state
        self.action_sequence1 = deque(maxlen=max_length)
        self.action_sequence2 = deque(maxlen=max_length)
        self.value_sequence = deque(maxlen=max_length)
        self.target_sequence = deque(maxlen=max_length)
        # self.action_sequence1.append(HOLD)
        # self.action_sequence2.append(HOLD2)
        # self.value_sequence.append(self.current_value)
        # self.target_sequence.extend([self.target_value] * len(self.value_sequence))

    def step(self, action, exploi):
        # Update current value based on action
        # if action == BLOW:
        #     self.current_value += 1
        # elif action == HOLD:
        #     pass
        # elif action == RELEASE:
        self.current_value = rssi
        # accuracy.append(self.target_value - self.current_value)
        accuracy.append(self.target_value)
        RSSI_ALL.append(rssi)
        exploIR.append(exploi)

        # Calculate the reward
        # reward = (self.target_value - self.prev_value) - (self.target_value - self.current_value)
        # reward = abs(self.target_value - self.current_value)
        cur_reward = abs(self.target_value - self.current_value)
        pre_reward = abs(self.target_value - self.prev_value)

        # the improvement compare to previous step
        improvement = cur_reward - pre_reward
        # the reward close to target
        # make the reward closer to target RSSI more sensitive
        a = self.target_value - math.log(max_reward/al, beta)
        b = self.target_value + math.log(max_reward/al, beta)
        rewardBelowTarget = pow(beta, self.current_value - a) * al
        rewardAboveTarget = pow(beta, b - self.current_value) * al
        if self.current_value < self.target_value:
            dis_reward = rewardBelowTarget
        else:
            dis_reward = rewardAboveTarget
        # dis_reward = max_reward - abs(self.target_value - self.current_value)

        reward = dis_reward + improvement
        # print(f"step rewards is {reward}")
        total_rewards.append(reward)


        # Check if the task is done
        # done = np.isclose(self.current_value, self.target_value, atol=0.01)
        # NEVER BE DONE ON LEARNING
        done = False

        self.prev_value = self.current_value

        # Format the State
        # Update action and value sequences
        self.action_sequence1.append(action[0])
        self.action_sequence2.append(action[1])
        # floor mean on state represent
        self.value_sequence.append(int(self.current_value))
        self.target_sequence.clear()
        self.target_sequence.extend([self.target_value] * len(self.value_sequence))

        return np.array([self.action_sequence1, self.action_sequence2, self.value_sequence, self.target_sequence]), reward, done, {}
        # return np.array([action_count_list, median_RSSI]), reward, done, {}

    def reset(self):
        self.current_value = self.prev_value
        self.action_sequence1.clear()
        self.action_sequence2.clear()
        self.value_sequence.clear()
        self.target_sequence.clear()
        # self.action_sequence1.append(HOLD)
        # self.action_sequence2.append(HOLD2)
        # self.value_sequence.append(self.current_value)
        self.target_sequence.extend([self.target_value] * len(self.value_sequence))
        return np.array([self.action_sequence1, self.action_sequence2, self.value_sequence, self.target_sequence])

    def render(self, mode='human'):
        print(f'Target Value: {self.target_value}, Current Value: {self.current_value}, Actions: {list(self.action_sequence)}, Values: {list(self.value_sequence)}')

class QLearningAgent:
    # single patch -- alpha=0.5, gamma=0.35, epsilon=0.7
    def __init__(self, action_space, alpha=alpha, gamma=gamma, epsilon=epsilon):
        self.action_space = action_space
        self.alpha = alpha # learning rate, the larger the alpha, the more the agent will consider the most recent information
        self.gamma = gamma # self.gamma is close to zero, the agent will tend to consider only immediate rewards
        self.epsilon = epsilon # exploration rate, the larger the epsilon, the more the agent will explore
        self.last_reward = -1
        self.ll_reward = -2
        self.last_action = (-1, -1)
        self.same_action_cnt = 0

        # Assume that the state space size is known and is small enough for a tabular representation.
        # You'll have to replace this with a function approximator (e.g., a neural network) if not.
        self.Q = {}

    def get_action(self, state):
        exploi = -1
        state = str(state.tolist())  # Convert state to string to use as dictionary key

        # Initialize Q-values to 0 if state is new
        if state not in self.Q:
            self.Q[state] = np.zeros((self.action_space[0].n, self.action_space[1].n))

        # if the last reward is not too bad, then hold and decrease the curiosity
        if self.last_reward >= max_reward:
            return (HOLD, HOLD2), exploi
        # stable condition towards target
        if self.last_reward > max_reward - 1:
            if np.random.uniform(0, 1) < 0.5:
                return (HOLD, HOLD2), exploi
            else:
                self.epsilon = 0.5
        else:
            self.epsilon = epsilon

        
        # Make the system to be stubborned when his action changed nothing and reward is low
        # stubborned_rate = 3 # hold action for X steps
        # if self.ll_reward == self.last_reward and self.last_reward < max_reward - 1 and self.same_action_cnt < stubborned_rate:
        #     print("STUBBORNED")
        #     return self.last_action

        # Epsilon-greedy action selection
        if np.random.uniform(0, 1) < self.epsilon:
            flat_index = self.action_space.sample()  # Exploration
            print(f"EXPLOR")
            return flat_index, exploi
        else:
            flat_index = np.argmax(self.Q[state]) # Exploitation
            # print("do what I learned!!!")
            # print(self.Q[state])
            # print(f"EXPLOI flatten index is {flat_index}")
            action_1 = flat_index // self.action_space[1].n
            action_2 = flat_index % self.action_space[1].n
            action = (action_1, action_2)
            # no learn, no move
            if self.Q[state][action] == 0: # if learned nothing
                print("EXPLOI nothing, HOLD")
                return (HOLD, HOLD2), exploi
            print("EXPLOI")
            exploi = 1
            return action, exploi
        
        

    def learn(self, state, action, reward, next_state, done):
        if self.last_action[0] == action[0] and self.last_action[1] == action[1]:
            self.same_action_cnt += 1
        else:
            self.same_action_cnt = 0
        self.ll_reward = self.last_reward
        self.last_reward = reward
        self.last_action = action

        state = str(state.tolist())  # Convert state to string to use as dictionary key
        next_state = str(next_state.tolist())  # Convert next_state to string to use as dictionary key

        # Initialize Q-values to 0 if states are new
        if state not in self.Q:
            self.Q[state] = np.zeros((self.action_space[0].n, self.action_space[1].n))
        if next_state not in self.Q:
            self.Q[next_state] = np.zeros((self.action_space[0].n, self.action_space[1].n))

        # Q-Learning update
        new_value = reward + self.gamma * np.max(self.Q[next_state]) if not done else reward
        self.Q[state][action] = (1 - self.alpha) * self.Q[state][action] + self.alpha * new_value
        print("learned!!!")
        print(f"On state: \n {state}")
        print(self.Q[state][action])




'''
Comunication to patch control system
'''
# 0:BLOW 1:HOLD 2:RELEASE
# dev = serial.Serial("/dev/cu.usbmodem101", baudrate=9600)
dev = serial.Serial("/dev/cu.usbmodem1301", baudrate=9600)

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
        print("reset the patch position...")
        pm.serial_send_syn(dev, (RELEASE, RELEASE2))
        sleep(8)
        print("start sending the stop signal")
        pm.serial_send(dev, "STOP")
        
        with open("patch_ability_range", "w") as file:
            file.write(f"upper bound: {tHighest}\n")
            file.write(f"lower bound: {tLowest}\n")
        print("strength test finished")
        target = input("Please enter the target RSSI. (To be Notice, the further target change please change the file patch_target_RSSI directly. To do the re-test, please rewrite 999 in the file patch_target_RSSI): ")
        if target == 999:
            test = 1
            test_start = time.time()
            tHighest = -100
            tLowest = 100
            test_blow_flag = 0
            continue
        with open("patch_target_RSSI", "w") as file:
            file.write(target)
    # Get a RSSI avg Data from arduino wifi board
    rssi, data_id_buff = pm.get_rssi_from_wifi_board(sock, addr, data_id_buff)
    if test == 1:
        print('Test RSSI:', rssi)
    elif pre_train == 1:
        print('Pre_train RSSI:', rssi)
    else:
        print('Current RSSI:', rssi)
    
    # loop, test mode & operating mode
    if test == 1: # test mode
        if test_blow_flag == 0:
            rev_message = pm.serial_send_syn(dev, (BLOW, BLOW2))
            test_blow_flag = 1
        if rssi > tHighest:
            tHighest = rssi
        if rssi < tLowest:
            tLowest = rssi
    elif pre_train == 1:
        RSSI_reset.append(rssi)
        if pre_train_cur < pre_train_num/2 - 1:
            # force agent to choose action and learn
            action = (BLOW, BLOW2)
            rev_message = pm.serial_send_syn(dev, action)
            next_state, reward, done, _ = env.step(action, -1)
            # agent.learn(state, action, reward, next_state, done)
            state = next_state
        elif pre_train_cur < pre_train_num/2 + 1:
            # force agent to choose action and learn
            action = (HOLD, HOLD2)
            rev_message = pm.serial_send_syn(dev, action)
            next_state, reward, done, _ = env.step(action, -1)
            # agent.learn(state, action, reward, next_state, done)
            state = next_state
        else:
            # force agent to choose action and learn
            action = (RELEASE, RELEASE2)
            rev_message = pm.serial_send_syn(dev, action)
            next_state, reward, done, _ = env.step(action, -1)
            # agent.learn(state, action, reward, next_state, done)
            state = next_state

        pre_train_cur += 1
        if pre_train_cur == pre_train_num: # end of pre_train
            print("Pretrain finished!!-----------------!!")
            pre_train = 0
            # target should be int to giving the repeatable state for q learning
            target = int(max(RSSI_reset) + goal) # goal is 1 for highest, -1 for lowest
            # target = statistics.median(RSSI_reset) + goal # goal is 1 for highest, -1 for lowest
            env.target_value = target
            if env.target_value != env.pre_target_value: # target changed, reset the environment
                env.pre_target_value = env.target_value
            RSSI_reset.clear()
            print(f"dynamic target changed to {target}")
            with open("patch_target_RSSI", "w") as file:
                file.write(str(target))
            
    else: # operating mode + RL learning mode
        # Retrieve the target RSSI
        with open("patch_target_RSSI", "r") as file:
            target = float(file.readline().strip())
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
                    # env.reset()
                    env.pre_target_value = env.target_value

            print("RL Target RSSI:", env.target_value)

        if dynamic_target == 1:
            RSSI_reset.append(rssi)
            target_try_cnt += 1
            if target_try_cnt >= target_try_cnt_max or rssi >= env.target_value:
                target_try_cnt = 0
                # assign target as the 10th largest RSSI
                # target should be int to giving the repeatable state for q learning
                target = int(max(RSSI_reset) + goal) # goal is 1 for highest, -1 for lowest
                # target = statistics.median(RSSI_reset) + goal # goal is 1 for highest, -1 for lowest
                env.target_value = target
                if env.target_value != env.pre_target_value: # target changed, reset the environment
                    env.pre_target_value = env.target_value
                RSSI_reset.clear()
                print(f"dynamic target changed to {target}")
                with open("patch_target_RSSI", "w") as file:
                    file.write(str(target))

        # RL learning
        if action[0] != -1:
            # The action is performed and the new state, reward, and done flag are received
            print(f"step exploi {exploi}")
            next_state, reward, done, _ = env.step(action, exploi)
            # The agent learns from the experience
            agent.learn(state, action, reward, next_state, done)
            # The new state becomes the current state for the next iteration
            state = next_state

        # The agent chooses an action
        action, exploi = agent.get_action(state)

        # move the patch
        # print(f"action is {action}")
        if action[0] != pre_action[0] and action[1] != pre_action[1]:
            pm.serial_send_syn(dev, action)
            pre_action = action

        
    sleep(1) # frequency





    '''
    When to stop the system?
    '''
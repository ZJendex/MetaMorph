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
import math

# Define the max reward
max_reward = 100
# Define the actions
BLOW = 0
HOLD = 1
RELEASE = 2
num_actions = 3
# Configuration
max_length = 20 # the memory of agent
episode_size = 100 # learning frequency

class MyEnvironment(gym.Env):
    def __init__(self, target_value, initial_value):
        super(MyEnvironment, self).__init__()

        self.action_space = spaces.Discrete(num_actions)  # BLOW, HOLD, RELEASE
        self.observation_space = spaces.Box(low=0, high=100, shape=(3, max_length), dtype=np.float32)  # action_count_list, RSSI_VALUE, target_RSSI
        # Initial setup
        self.target_value = target_value
        self.pre_target_value = target_value
        self.current_value = initial_value
        self.prev_value = self.current_value
        self.steps = 0
        self.max_length = max_length # the memory of agent
        self.episode_size = episode_size # learning frequency
        self.num_actions = num_actions
        # State Information
        # Temporary use action sequence and value sequence to represent the state
        # In the future, we can use the detailed floor plan image + air prerssure of each patch to represent the state

        # Ensure the length to be max_length 
        self.action_sequence = deque(maxlen=max_length) # dimX for x number of patches
        self.value_sequence = deque(maxlen=max_length)
        self.target_sequence = deque(maxlen=max_length)
        self.action_sequence.append(HOLD)
        self.value_sequence.append(self.current_value)
        self.target_sequence.append(self.target_value)


    def step(self, action, rssi):
        self.steps += 1
        # Update current value based on action
        # if action == BLOW:
        #     self.current_value += 1
        # elif action == HOLD:
        #     pass
        # elif action == RELEASE:
        self.current_value = rssi

        # Calculate the reward
        # reward = 100 - abs(self.target_value - self.current_value)

        # make the reward closer to target RSSI more sensitive
        beta = 1.077 # the closer to 1.1
        alpha = 30 # the larger to 100
        a = self.target_value - math.log(max_reward/alpha, beta)
        b = self.target_value + math.log(max_reward/alpha, beta)
        rewardBelowTarget = pow(beta, self.current_value - a) * alpha
        rewardAboveTarget = pow(beta, b - self.current_value) * alpha
        if self.current_value < self.target_value:
            cur_reward = rewardBelowTarget
        else:
            cur_reward = rewardAboveTarget
        
        # the system shouldn't get reward if it's as same close to target as before
        # therefore we need to substruct the cur to pre
        rewardBelowTarget = pow(beta, self.prev_value - a) * alpha
        rewardAboveTarget = pow(beta, b - self.prev_value) * alpha
        if self.prev_value < self.target_value:
            pre_reward = rewardBelowTarget
        else:
            pre_reward = rewardAboveTarget

        reward = cur_reward - pre_reward
        print(f"step rewards is {reward}")

        # Check if the task is done
        # Stratige 1: Finish when RSSI value sequence has mean almost equal to the target
        # done = np.isclose(sum(self.value_sequence)/len(self.value_sequence), self.target_value, atol=1)
        # Stratige 2: Finish when the number of steps exceeds 20
        if self.steps >= self.episode_size:
            done = True
            self.steps = 0
        else:
            done = False

        self.prev_value = self.current_value

        # Format the State
        self.action_sequence.append(action)
        self.value_sequence.append(self.current_value)
        self.target_sequence.clear()
        self.target_sequence.extend([self.target_value] * len(self.value_sequence))

        return np.array([self.action_sequence, self.value_sequence, self.target_sequence]), reward, done, {}
        # return np.array([action_count_list, median_RSSI]), reward, done, {}

    def reset(self):
        self.current_value = self.prev_value
        self.action_sequence.append(HOLD)
        self.value_sequence.append(self.current_value)
        self.target_sequence.append(self.target_value)
        return np.array([self.action_sequence, self.value_sequence, self.target_sequence])

    def get_state(self):
        return np.array([self.action_sequence, self.value_sequence, self.target_sequence])

    def render(self, mode='human'):
        print(f'Target Value: {self.target_value}, Current Value: {self.current_value}, Actions: {list(self.action_sequence)}, Values: {list(self.value_sequence)}')

class PolicyNetwork(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(PolicyNetwork, self).__init__()
        self.fc1 = nn.Linear(input_dim, 128) # Fully connected layer with 128 units
        self.fc2 = nn.Linear(128, output_dim)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.softmax(self.fc2(x), dim=0)
        return x

class PolicyGradientAgent:
    def __init__(self, input_dim, output_dim, learning_rate=0.01):
        self.network = PolicyNetwork(input_dim, output_dim)
        self.optimizer = optim.Adam(self.network.parameters(), lr=learning_rate)
        self.log_probs = []
        self.rewards = []

    def get_action(self, state):
        # Flatten the state array
        print("the state is ")
        print(state)
        state = torch.tensor(state, dtype=torch.float32).flatten()
        action_probs = self.network(state)
        print("action prob is")
        print(action_probs)
        action_distribution = torch.distributions.Categorical(action_probs)
        action = action_distribution.sample()
        self.log_probs.append(action_distribution.log_prob(action))
        return action.item()

    def record_rewards(self, reward):
        self.rewards.append(reward)

    def learn(self):
        accumulated_rewards = []
        G = 0
        for r in self.rewards[::-1]:
            G = r + 0.99 * G
            accumulated_rewards.insert(0, G)
        
        # Normalize the accumulated rewards
        accumulated_rewards = torch.tensor(accumulated_rewards)
        accumulated_rewards = (accumulated_rewards - accumulated_rewards.mean()) / (accumulated_rewards.std() + 1e-9)
        
        loss = []
        for log_prob, G in zip(self.log_probs, accumulated_rewards):
            loss.append(-log_prob * G)
            
        self.optimizer.zero_grad()
        loss = torch.stack(loss).sum()
        loss.backward()
        self.optimizer.step()
        total_rewards = sum(self.rewards)

        # Clear the memory
        self.log_probs = []
        self.rewards = []

        return total_rewards, loss.item()
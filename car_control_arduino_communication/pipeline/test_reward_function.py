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
import math

target_value = -27
current_value = -27
max_reward = 100

beta = 1.077 # the closer to 1.1
alpha = 30 # the larger to 100
a = target_value - math.log(max_reward/alpha, beta)
b = target_value + math.log(max_reward/alpha, beta)
rewardBelowTarget = pow(beta, current_value - a) * alpha
rewardAboveTarget = pow(beta, b - current_value) * alpha
if current_value < target_value:
    reward = rewardBelowTarget
else:
    reward = rewardAboveTarget

print(f"the reward is {reward}")
print(f"where a is {a}, b is {b}")

cur_values = np.linspace(-100, 0, 50000)
cur_left = np.linspace(-100, target_value, 10000)
cur_right = np.linspace(target_value, 0, 10000)
rewardBelowTarget = pow(beta, cur_left - a) * alpha
rewardAboveTarget = pow(beta, b - cur_right) * alpha

# Plot
plt.plot(cur_left, rewardBelowTarget, label='Reward Below Target')
plt.plot(cur_right, rewardAboveTarget, label='Reward Above Target')
plt.xlabel('Current Value')
plt.ylabel('Reward')
plt.legend()
plt.title('Reward Functions')
plt.grid(True)
plt.show()









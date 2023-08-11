import subprocess
import os
import numpy as np
import matplotlib.pyplot as plt

loc = 2
target_patch = "2*12"
data_directory = "../data/Aug11"  # Replace with the directory path
noise_indicator_all = 0
for i in range(1, 4):
    filename = "rssi_data_delay_test_empty_loc" + str(loc) + "_r" + str(i) + ".txt"
    data_file = os.path.join(data_directory, filename)

    with open(data_file, 'r') as file:
        lines = file.readlines()  
        # rssi_data_points = [int(line.strip()) for line in lines]
        rssi_data_points = []
        for line in lines:
            if line.strip() != '':
                rssi_data_points.append(int(line.strip()))

    time = rssi_data_points[-1] # total ms
    rssi_data_points = rssi_data_points[:-2]
    rssi_data_points = np.array(rssi_data_points)

    noise_indicator = np.std(rssi_data_points)
    noise_indicator_all += noise_indicator
noise_indicator_all /= 3
noise_indicator = noise_indicator_all
print(f"Retrieved from the empty loc" + str(loc))
print(f"Standard Deviation (Noise Indicator): {noise_indicator:.3f} dB")

file_names = [file for file in os.listdir(data_directory) if file.endswith(".txt")]
for filename in file_names:
    if filename.startswith("rssi_data_delay_test_" + target_patch + "_loc" + str(loc)):
        data_file = os.path.join(data_directory, filename)
        with open(data_file, 'r') as file:
            lines = file.readlines()  
            # rssi_data_points = [int(line.strip()) for line in lines]
            rssi_data_points = []
            for line in lines:
                if line.strip() != '':
                    rssi_data_points.append(int(line.strip()))

        time = rssi_data_points[-1] # total ms
        interval = time/rssi_data_points[-2]
        rssi_data_points = rssi_data_points[:-2]
        rssi_data_points = np.array(rssi_data_points)
        # Smooth the data
        avg = 5 # will eliminate the last avg data points
        rssi_smooth_data_points = []
        for i in range(len(rssi_data_points) - avg):
            rssi_smooth_data_points.append(np.mean(rssi_data_points[i:i+avg]))

        delay_point = -1
        for i in range(len(rssi_smooth_data_points)):
            # if rssi_smooth_data_points[i] > np.median(rssi_smooth_data_points[0:i+1]) + noise_indicator or rssi_smooth_data_points[i] < np.mean(rssi_smooth_data_points[0:i]) - noise_indicator:
            if rssi_smooth_data_points[i] > rssi_smooth_data_points[0] + noise_indicator or rssi_smooth_data_points[i] < rssi_smooth_data_points[0] - noise_indicator:
                delay_point = i
                break

        time_delay = delay_point * interval

        print(f"Target the file {filename}")
        print(f"the delay is {time_delay:.3f} ms")

# target_filename = "rssi_data_delay_test_2*4_loc1_r1.txt"
# data_file = os.path.join(data_directory, filename)
# with open(data_file, 'r') as file:
#     lines = file.readlines()  
#     # rssi_data_points = [int(line.strip()) for line in lines]
#     rssi_data_points = []
#     for line in lines:
#         if line.strip() != '':
#             rssi_data_points.append(int(line.strip()))

# time = rssi_data_points[-1] # total ms
# interval = time/rssi_data_points[-2]
# rssi_data_points = rssi_data_points[:-2]
# rssi_data_points = np.array(rssi_data_points)

# # Smooth the data
# avg = 5 # will eliminate the last avg data points
# rssi_smooth_data_points = []
# for i in range(len(rssi_data_points) - avg):
#     rssi_smooth_data_points.append(np.mean(rssi_data_points[i:i+avg]))

# delay_point = -1
# for i in range(len(rssi_smooth_data_points)):
#     if rssi_smooth_data_points[i] > np.mean(rssi_smooth_data_points[0:i]) + noise_indicator or rssi_smooth_data_points[i] < np.mean(rssi_smooth_data_points[0:i]) - noise_indicator:
#         delay_point = i
#         break

# time_delay = delay_point * interval

# print(f"Target the file {target_filename}")
# print(f"the delay is {time_delay:.3f} ms")


import subprocess
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline, BSpline



data_directory = "../data/July20 30tile"  # Replace with the directory path
# Get all file names in the directory
file_names = [file for file in os.listdir(data_directory) if file.endswith(".txt")]
print(file_names)

total_RSSI = 0
total_cnt = 0
for filename in file_names:
    if filename.startswith("rssi_data_car_bending"):
        data_file = os.path.join(data_directory, filename)
        print(data_file)

        # Plot the data
        with open(data_file, 'r') as file:
            lines = file.readlines()  
            # rssi_data_points = [int(line.strip()) for line in lines]
            rssi_data_points = []
            for line in lines:
                if line.strip() != '':
                    rssi_data_points.append(int(line.strip()))
        
        time = int(rssi_data_points[-1]/1000)
        rssi_data_points = rssi_data_points[:-2]
        rssi_data_points = np.array(rssi_data_points)
        print(rssi_data_points)
        print("The duration is " + str(time) + "s")
        length = len(rssi_data_points)
        mean = rssi_data_points.mean()
        print(filename + " length is : " + str(length))
        total_cnt += length
        print(filename + " mean is : " + str(mean))
        total_RSSI += sum(rssi_data_points)
print(total_cnt)
print(total_RSSI)
print(str(total_RSSI/total_cnt))

        

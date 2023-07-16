import subprocess
import os
import numpy as np
import matplotlib.pyplot as plt
import time
from collections import deque



data_directory = "../data/July13"  # Replace with the directory path
plot_directory = "../plot/July13"
# Get all file names in the directory
file_names = [file for file in os.listdir(data_directory) if file.endswith(".txt")]
print(file_names)

for filename in file_names:
    if filename.startswith("rssi_data_car_bending_2*12_loc1_r2"):
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
        
        duration = int(rssi_data_points[-1]/1000)
        rssi_data_points = rssi_data_points[:-2]
        rssi_data_points = np.array(rssi_data_points)
        print(rssi_data_points)
        print("The duration is " + str(duration) + "s")
        # Smooth the data
        avg = 20
        rssi_smooth_data_points = []
        for i in range(avg, len(rssi_data_points)):
            rssi_smooth_data_points.append(np.mean(rssi_data_points[i-avg:i]))

        times = np.linspace(0, duration, len(rssi_smooth_data_points))

        # # Plot the data
        # plt.plot(times, rssi_data_points)
        plt.plot(times, rssi_smooth_data_points)

        # Set labels and title
        plt.xlabel('Time (s)')
        plt.ylabel('RSSI')
        plt.title(filename[:-3])
        plt.show()
        
        dy_dx = np.diff(rssi_smooth_data_points) / np.diff(times)
        times = np.linspace(0, duration, len(rssi_smooth_data_points)-1)
        plt.plot(times, dy_dx)
        plt.title("derivation")
        plt.show()

        # Monitor the data window to find the patch start and end point
        x = np.linspace(0, 100, 100)
        rssi_data_head_slope = []
        rssi_data_tail_slope = []
        for i in range(101, len(rssi_smooth_data_points)-101):           
            head = rssi_smooth_data_points[i-101:i-1]
            tail = rssi_smooth_data_points[i+1:i+101]
            slopeH, intercept = np.polyfit(x, head, deg=1)
            slopeT, _ = np.polyfit(x, tail, deg=1)
            rssi_data_head_slope.append(slopeH)
            rssi_data_tail_slope.append(slopeT)
            if i == 500:
                # Generate points on the regression line
                regression_x = np.array([min(x), max(x)])
                regression_y = slopeH * regression_x + intercept
                # Plot the data and regression line
                plt.scatter(x, head, color='blue', label='Data')
                plt.plot(regression_x, regression_y, color='red', label='Regression Line')
                plt.title("Slope is " + str(slopeH))
                plt.show()

        times = np.linspace(0, len(rssi_data_head_slope),len(rssi_data_head_slope))

        # # Plot the data
        # plt.plot(times, rssi_data_points)
        plt.plot(times, rssi_data_head_slope)
        plt.show()
        plt.plot(times, rssi_data_tail_slope)
        plt.show()
        # Show the plot
        plt.show()
        # # # Save the plot
        # plot_file = os.path.join(plot_directory, filename)
        # path = plot_file[:-3] + "png"
        # plt.savefig(path, dpi=300)
        # plt.close()
        

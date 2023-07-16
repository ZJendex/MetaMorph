import subprocess
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline, BSpline



data_directory = "../data/July13"  # Replace with the directory path
plot_directory = "../plot/July13"
# Get all file names in the directory
file_names = [file for file in os.listdir(data_directory) if file.endswith(".txt")]
print(file_names)

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
        # Smooth the data
        avg = 20
        rssi_smooth_data_points = []
        for i in range(avg, len(rssi_data_points)):
            rssi_smooth_data_points.append(np.mean(rssi_data_points[i-avg:i]))

        times = np.linspace(0, time, len(rssi_smooth_data_points))

        # # Plot the data
        # plt.plot(times, rssi_data_points)
        plt.plot(times, rssi_smooth_data_points)

        # Set labels and title
        plt.xlabel('Time (s)')
        plt.ylabel('RSSI')
        plt.title(filename[:-3])

        # Show the plot
        # plt.show()

        # # Save the plot
        plot_file = os.path.join(plot_directory, filename)
        path = plot_file[:-3] + "png"
        plt.savefig(path, dpi=300)
        plt.close()
        

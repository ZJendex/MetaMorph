import subprocess
import re
import numpy as np
import matplotlib.pyplot as plt
import math
import lib.jpgToArr as jpgToArr
from scipy.interpolate import griddata
import cv2
import matplotlib.colors as mcolors
from datetime import datetime
import readline
from scipy.interpolate import Rbf
from collections import deque
import lib.retrieve_signal_strength as retrieve_signal_strength
import time
import subprocess
import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import make_interp_spline, BSpline
import colormap

# floor plan vertices
L_Locations = [[95, 318], [538, 318], [538, 469], [682, 469], [682, 576], [919, 576], [919, 714], [341, 714], [341, 486], [100, 486]]
vertices = np.array([L_Locations], dtype=np.int32)
valid_area_mask = np.zeros((1000, 1000))
outline_mask = np.zeros((1000, 1000))
cv2.polylines(outline_mask, vertices, isClosed=True, color=1, thickness=7)
cv2.fillPoly(valid_area_mask, vertices, 1)
floor_map = jpgToArr.getCompressedJpgToGreyArr('floor_plan_res/smallfb_compressed_image2.jpg')


RSSI_LIMIT = [-10, 10]
tx_loc = [486, 524]
RSSI_data_location = [[111, 358],  [263, 358], [376, 358], [514, 358], [372, 498], [510, 467], [663, 467], [888, 590], [793, 590], [656, 590], [517, 590], [364, 590], [888, 686], [793, 686], [656, 686], [517, 686], [364, 686]]
wifi_RSSI_data = []


RSSI_data_location = [sublist[::-1] for sublist in RSSI_data_location] # invert the x, y axis to match with interpolation axis
'''
return[0] true if there is a neighbor that is not nan
return[1] 1: x-1, 2: x+1, 3: y-1, 4: y+1
'''
def findEmptyNeighbor(nan_locations, i, j, valid_area_mask):
    if i-1 >= 0 and valid_area_mask[i-1][j] and nan_locations[i-1][j]:
        return True, 1
    if i+1 < len(nan_locations) and valid_area_mask[i+1][j] and nan_locations[i+1][j]:
        return True, 2
    if j-1 >= 0 and valid_area_mask[i][j-1] and nan_locations[i][j-1]:
        return True, 3
    if j+1 < len(nan_locations[0]) and valid_area_mask[i][j+1] and nan_locations[i][j+1]:
        return True, 4
    return False, 0
def plot_save(wifi_RSSI_data, RSSI_data_location, floor_map, valid_area_mask, outline_mask, path, show_detail=False, interpolate_cornor=False, extropolation=False):
    #----------------- plot -----------------
    # Create the grid on which to perform the interpolation
    grid_x, grid_y = np.mgrid[0:1000, 0:1000]
    # fill the corners of grid with RSSI_LIMIT[0] to make sure the interpolation map through the whole area
    if interpolate_cornor:
        RSSI_data_location.append([0, 0])
        RSSI_data_location.append([0, 999])
        RSSI_data_location.append([999, 0])
        RSSI_data_location.append([999, 999])
        wifi_RSSI_data.append(RSSI_LIMIT[0])
        wifi_RSSI_data.append(RSSI_LIMIT[0])
        wifi_RSSI_data.append(RSSI_LIMIT[0])
        wifi_RSSI_data.append(RSSI_LIMIT[0])
    # If rssi data locs are all in the same line, griddate can not interpolate
    # To enable interpolation, we gonna change the last data point on the line to have 1 unit upward
    # Extract the coordinates from the locations
    y_coordinates = [location[1] for location in RSSI_data_location]
    x_coordinates = [location[0] for location in RSSI_data_location]
    # Check if all y-coordinates are the same
    if all(y == y_coordinates[0] for y in y_coordinates):
        RSSI_data_location[-1] = [RSSI_data_location[-1][0], RSSI_data_location[-1][1]+1]
    if all(x == x_coordinates[0] for x in x_coordinates):
        RSSI_data_location[-1] = [RSSI_data_location[-1][0]+1, RSSI_data_location[-1][1]]
    # Perform the interpolation
    rssi_grid = griddata(RSSI_data_location, wifi_RSSI_data, (grid_x, grid_y), method='linear')

    if extropolation:
        # Extrolation base on free-space path loss model
        known_points = deque(np.argwhere(~np.isnan(rssi_grid)))
        # BFS to fill the grid
        while known_points:
            x, y = known_points.popleft()

            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy

                if 0 <= nx < 1000 and 0 <= ny < 1000 and np.isnan(rssi_grid[nx, ny]):
                    # Find the neighbors that have values
                    neighbors = [(nx + dx, ny + dy) for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)] 
                                if 0 <= nx + dx < 1000 and 0 <= ny + dy < 1000 and not np.isnan(rssi_grid[nx + dx, ny + dy])]

                    if neighbors:
                        d = np.sqrt((tx_loc[0] - nx)*(tx_loc[0] - nx) + (tx_loc[1] - ny) * (tx_loc[1] - ny)) 
                        # free-space path loss model
                        mean_dbm = np.mean([rssi_grid[nx, ny] for nx, ny in neighbors])
                        mean_power = pow(10, mean_dbm/10)/1000
                        if(d > 0):
                            rst_power = mean_power / (((d+1)/d)*((d+1)/d))
                            rssi_grid[nx, ny] = 10 * math.log(rst_power, 10) + 30
                        else:
                            rssi_grid[nx, ny] = mean_dbm
                        # Add this point to the queue to process its neighbors
                        known_points.append((nx, ny))


    nan_locations = np.isnan(rssi_grid)

    if show_detail:
        for i in range(len(rssi_grid)):
            for j in range(len(rssi_grid[0])):
                if floor_map[i][j] != 1 or outline_mask[i][j] == 1:
                    rssi_grid[i][j] = RSSI_LIMIT[0]*10
                elif valid_area_mask[i][j] == 0: # clean invalid area
                    rssi_grid[i][j] = None
                continue
    else:      
        for i in range(len(rssi_grid)):
            for j in range(len(rssi_grid[0])):
                # plot with detailed floor map
                # if floor_map[i][j] != 1 or outline_mask[i][j] == 1:
                if outline_mask[i][j] == 1: # draw outline
                    rssi_grid[i][j] = RSSI_LIMIT[0]*10
                # elif valid_area_mask[i][j] == 1 and nan_locations[i][j]: # stright supplement valid area
                #     rssi_grid[i][j] = -42
                elif valid_area_mask[i][j] == 0: # clean invalid area
                    rssi_grid[i][j] = None

                continue

    # Create a figure
    fig, ax = plt.subplots()
    # Now create a custom colormap
    # cmap = mcolors.LinearSegmentedColormap.from_list("", ["#ea8c55", "#c75146", "#ad2e24", "#81171b", "#540804"])
    # cmap = mcolors.LinearSegmentedColormap.from_list("", ["#eb3434", "#eb9b34", "#ebeb34", "#7aeb34", "#34ebd2", "#347aeb", "#9834eb", "#eb34cc"])
    # cmap = mcolors.LinearSegmentedColormap.from_list("", ["#9700fc", "#1900fc", "#00cafc", "#00fc16", "#e3fc00", "#fc9c00", "#fc0d00"])
    # Wuhuarou
    cmap = mcolors.LinearSegmentedColormap.from_list("", ["#4D0500", "#FF2104", "#FEDF00", "#FDFD8E"])
    # cmap = mcolors.LinearSegmentedColormap.from_list("", ["#ffffff", "#000000"])
    # cmap = colormap.parula
    cmap.set_under('black')
    img = ax.imshow(rssi_grid, cmap=cmap, vmin=RSSI_LIMIT[0]*2)
    # viridis = plt.cm.get_cmap('parula', 256)
    # viridis.set_under('black')  # Color for values less than vmin
    # img = ax.imshow(rssi_grid, cmap=viridis, vmin=RSSI_LIMIT[0]*2)
    # Create a colorbar, ignoring the lowest value (0 in this case)
    plt.colorbar(img, ax=ax)
    img.set_clim(RSSI_LIMIT[0], RSSI_LIMIT[1])
    plt.savefig(path, dpi=300)
    plt.close()

data_directory = "data/"  # Replace with the directory path
plot_directory = "plot/"
fileName_startwite = ""
smooth_rate = 50
# Get all file names in the directory
file_names = [file for file in os.listdir(data_directory) if file.endswith(".txt")]

baseline = []
for filename in file_names:
    if filename == "empty.txt":
        data_file = os.path.join(data_directory, filename)
        print(data_file)
        with open(data_file, 'r') as file:
            lines = file.readlines()  
            wifi_RSSI_data = []
            for line in lines:
                if line.strip() != '':
                    wifi_RSSI_data.append(float(line.strip()))
            
            print(f"Read data length {len(wifi_RSSI_data)}")
        baseline = wifi_RSSI_data
        break

for filename in file_names:
    if filename == "empty.txt":
        continue
    data_file = os.path.join(data_directory, filename)
    print(data_file)
    with open(data_file, 'r') as file:
        lines = file.readlines()  
        wifi_RSSI_data = []
        for line in lines:
            if line.strip() != '':
                wifi_RSSI_data.append(float(line.strip()) - baseline[len(wifi_RSSI_data)])
        
        print(f"Read data length {len(wifi_RSSI_data)}")
    
    # plotDE
    name = filename[:-4] + "_DE_backgroundExtraction" + ".png"
    figurePath = data_file = os.path.join(plot_directory, name)
    print(f"plotDE at path {figurePath}")
    plot_save(wifi_RSSI_data, RSSI_data_location, floor_map, valid_area_mask, outline_mask, figurePath, show_detail=True, extropolation=True)
    # # plotD
    # name = filename[:-4] + "_D_backgroundExtraction" + ".png"
    # figurePath = data_file = os.path.join(plot_directory, name)
    # print(f"plotDE at path {figurePath}")
    # plot_save(wifi_RSSI_data, RSSI_data_location, floor_map, valid_area_mask, outline_mask, figurePath, show_detail=True)
    


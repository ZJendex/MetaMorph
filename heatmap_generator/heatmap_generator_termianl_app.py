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

def plot_show(wifi_RSSI_data, RSSI_data_location, floor_map, valid_area_mask, outline_mask, show_detail=False, interpolate_cornor=False, extropolation=False):
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
    cmap = mcolors.LinearSegmentedColormap.from_list("", ["#9700fc", "#1900fc", "#00cafc", "#00fc16", "#e3fc00", "#fc9c00", "#fc0d00"])
    cmap.set_under('black')
    img = ax.imshow(rssi_grid, cmap=cmap, vmin=RSSI_LIMIT[0]*2)
    # viridis = plt.cm.get_cmap('viridis', 256)
    # viridis.set_under('black')  # Color for values less than vmin
    # img = ax.imshow(rssi_grid, cmap=viridis, vmin=RSSI_LIMIT[0]*2)
    # Create a colorbar, ignoring the lowest value (0 in this case)
    plt.colorbar(img, ax=ax)
    img.set_clim(RSSI_LIMIT[0], RSSI_LIMIT[1])
    plt.show()

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
    cmap = mcolors.LinearSegmentedColormap.from_list("", ["#9700fc", "#1900fc", "#00cafc", "#00fc16", "#e3fc00", "#fc9c00", "#fc0d00"])
    cmap.set_under('black')
    img = ax.imshow(rssi_grid, cmap=cmap, vmin=RSSI_LIMIT[0]*2)
    # viridis = plt.cm.get_cmap('viridis', 256)
    # viridis.set_under('black')  # Color for values less than vmin
    # img = ax.imshow(rssi_grid, cmap=viridis, vmin=RSSI_LIMIT[0]*2)
    # Create a colorbar, ignoring the lowest value (0 in this case)
    plt.colorbar(img, ax=ax)
    img.set_clim(RSSI_LIMIT[0], RSSI_LIMIT[1])
    plt.savefig(path, dpi=300)
    plt.close()

def move(loc, cmd):
    direction = loc[2]

    if cmd == "L":
        direction = (direction - 1) % 4
    elif cmd == "R":
        direction = (direction + 1) % 4
    elif cmd == "F":
        if direction == 0:
            loc[1] -= one_meter_distance
        elif direction == 1:
            loc[0] += one_meter_distance
        elif direction == 2:
            loc[1] += one_meter_distance
        elif direction == 3:
            loc[0] -= one_meter_distance
    elif cmd == "B":
        if direction == 0:
            loc[1] += one_meter_distance
        elif direction == 1:
            loc[0] -= one_meter_distance
        elif direction == 2:
            loc[1] -= one_meter_distance
        elif direction == 3:
            loc[0] += one_meter_distance
    loc[2] = direction
    return loc


# floor plan vertices
L_Locations = [[163, 150], [384, 116], [442, 577], [442, 663], [396, 663], [396, 722], [640, 722], [640, 572], [552, 572], [552, 500], [583, 500], [583, 402], [600, 428], [795, 428], [795, 560], [846, 560], [846, 900], [535, 900], [535, 878], [483, 878], [483, 900], [197, 900], [199, 508], [163, 150]]
vertices = np.array([L_Locations], dtype=np.int32)
valid_area_mask = np.zeros((1000, 1000))
outline_mask = np.zeros((1000, 1000))
cv2.polylines(outline_mask, vertices, isClosed=True, color=1, thickness=7)
cv2.fillPoly(valid_area_mask, vertices, 1)
floor_map = jpgToArr.getCompressedJpgToGreyArr('floor_plan_res/compressed_image2.jpg')

'''
TODO: 
'''
# Rx location should always sample the corners of the valid area to make sure the interpolation map through the valid area
RSSI_data_location = [] # TODO: init Rx location
wifi_RSSI_data = []
data_start = 0 # crop data to calculate the rssi data for coreresponding route of car
RSSI_LIMIT = [-60, 0] # TODO: init RSSI limit
tx_loc = [507, 780] # TODO: init Tx location for extropolation
tx_loc = [780, 507] # TODO: inverse tx_loc to match the map set
tx_loc = [770, 214]
directory = "data/"     # TODO: init directory to save data and plot
data_file = 'rssi_data_car.txt'  # TODO loading data path
one_meter_distance = 17 # TODO: init one meter distance

car_start = [0, 0, 0] # North 0, East 1, South 2, West 3 -- (x, y, direction)
# 507 780 1 and 3
# 381 750 0
# wifi_RSSI_data = [-45, -40, -49, -43]
# RSSI_data_location = [[197, 900], [846, 900], [151, 40], [690, 40]]

# wifi_RSSI_data = [-10, -30, -60, -87]
# RSSI_data_location = [[328, 840], [338, 840], [328, 830], [338, 830]]

# wifi_RSSI_data = np.random.uniform(-50, -40, 24).tolist()
# RSSI_data_location = L_Locations

RSSI_data_location = [[220, 771], [273, 771], [333, 771], [333, 859], [396, 771], [390, 859], [424, 801], [424, 890], [477, 890], [477, 801], [450, 771], [511, 771], [568, 771], [568, 817], [629, 817], [641, 771], [694, 771], [694, 706], [714, 706], [714, 883], [831, 883], [774, 788], [831, 714], [831, 624], [775, 624], [714, 624], [661, 624], [701, 549], [652, 549], [645, 454], [702, 452], [776, 452], [382, 669], [335, 669], [276, 669], [221, 669], [211, 616], [205, 566], [268, 557], [333, 549], [301, 464], [340, 450], [411, 444], [409, 387], [397, 321], [394, 258], [324, 271], [393, 248], [378, 127], [310, 231], [308, 143], [265, 154], [272, 237], [267, 313], [190, 326], [297, 355], [313, 410]]
wifi_RSSI_data = []

# wifi_RSSI_data = np.random.uniform(-50, -40, 100).tolist()
# RSSI_data_location = [[i, j] for i in range(0, 1000, 100) for j in range(0, 1000, 100)]

RSSI_data_location = [sublist[::-1] for sublist in RSSI_data_location] # invert the x, y axis to match with interpolation axis
pop_buffer = []
program_id = time.time()
while True:
    user_input = input("Please enter a command: ")
    if user_input == "":
        n = 25
        total_rssi = 0
        for i in range(n):
            rssi = int(retrieve_signal_strength.getCurrentWifiSignalInfo(raw=False))
            print(f"cur rssi is {rssi}")
            total_rssi += rssi
            time.sleep(0.2)
        cur_rssi = total_rssi / n
        print(cur_rssi)
        wifi_RSSI_data.append(cur_rssi)
        with open(f'data/wifi_RSSI_data{program_id}.txt', 'a') as file:
            file.write(str(cur_rssi))
            file.write("\n")
    elif user_input == ".":
        print(getCurrentWifiSignalInfo(raw=True))
    elif user_input == "show":
        print("Current data: ", wifi_RSSI_data)
        print(f"with length {len(wifi_RSSI_data)}")
    elif user_input == "showL":
        print("Current locations: ", RSSI_data_location)
        print(f"with length {len(RSSI_data_location)}")
    elif user_input == "-":
        if(len(wifi_RSSI_data) == 0):
            print("No data in the buffer. Please add data first.")
            continue
        pop_buffer.append(wifi_RSSI_data.pop())
        print("Last data removed. Current data: ", wifi_RSSI_data)
    elif user_input == "+":
        if(len(pop_buffer) == 0):
            print("No data in the buffer. Please add data first.")
            continue
        wifi_RSSI_data.append(pop_buffer.pop())
        print("Last data added. Current data: ", wifi_RSSI_data)
    elif user_input == "plot":
        if(len(wifi_RSSI_data) != len(RSSI_data_location)):
            print("The number of data points {} does not match the number of locations {}.".format(len(wifi_RSSI_data), len(RSSI_data_location)))
            continue
        
        plot_show(wifi_RSSI_data, RSSI_data_location, floor_map, valid_area_mask, outline_mask)
    elif user_input == "plotD":
        if(len(wifi_RSSI_data) != len(RSSI_data_location)):
            print("The number of data points {} does not match the number of locations {}.".format(len(wifi_RSSI_data), len(RSSI_data_location)))
            continue
        
        plot_show(wifi_RSSI_data, RSSI_data_location, floor_map, valid_area_mask, outline_mask, show_detail=True)
    elif user_input == "plotDI":
        if(len(wifi_RSSI_data) != len(RSSI_data_location)):
            print("The number of data points {} does not match the number of locations {}.".format(len(wifi_RSSI_data), len(RSSI_data_location)))
            continue
        
        plot_show(wifi_RSSI_data, RSSI_data_location, floor_map, valid_area_mask, outline_mask, show_detail=True, interpolate_cornor=True)
    elif user_input == "plotDE":
        if(len(wifi_RSSI_data) != len(RSSI_data_location)):
            print("The number of data points {} does not match the number of locations {}.".format(len(wifi_RSSI_data), len(RSSI_data_location)))
            continue
        
        plot_show(wifi_RSSI_data, RSSI_data_location, floor_map, valid_area_mask, outline_mask, show_detail=True, extropolation=True)
    elif user_input == "savePlotDE":
        if(len(wifi_RSSI_data) != len(RSSI_data_location)):
            print("The number of data points {} does not match the number of locations {}.".format(len(wifi_RSSI_data), len(RSSI_data_location)))
            continue
        path = data_file[:-3] + "png"
        plot_save(wifi_RSSI_data, RSSI_data_location, floor_map, valid_area_mask, outline_mask, path, show_detail=True, extropolation=True)
    elif user_input.startswith("f"):
        data_file = user_input.split()[1]
        print("data file path is " + data_file)
    # set the car start location and direction
    elif user_input.startswith("start "):
        info = user_input.split()
        if(len(info) < 4):
            print("Please enter locationX and locationY and direction.")
            continue
        locationX = info[1]
        locationY = info[2]
        direction = info[3]
        car_start = [int(locationX), int(locationY), int(direction)]
    # load car commands and retrieve the rssi data from the file
    # car command should only move with 1 meter or turn 90 degree
    # if load success, wifi_RSSI_data and RSSI_data_location should be overwritten
    elif user_input.startswith("load "):
        car_commands = user_input.split()[1:] # from 1 to len()
        if car_start[0] == 0:
            print("Please set the car start location first.")
            continue
        # with open(data_file, 'r') as file:
        #     line = file.readline()  
        #     rssi_data_points = line.split()[data_start:] 
        with open(data_file, 'r') as file:
            lines = file.readlines()  
            rssi_data_points = [int(line.strip()) for line in lines]
            rssi_data_points = rssi_data_points[data_start:]
        
        print("received rssi data points " + str(len(rssi_data_points)) + " with commands " + str(len(car_commands)))
        print("data points " + str(rssi_data_points))
        print("commands " + str(car_commands))
        for i in range(len(rssi_data_points)):
            rssi_data_points[i] = int(rssi_data_points[i])
        
        loc = car_start
        # RSSI_data_location = []
        # wifi_RSSI_data = []
        len_cmd = 0
        for i in range(0, len(car_commands)):
            if car_commands[i].startswith("F"):
                loc = move(loc, "F")
                RSSI_data_location.append([loc[1], loc[0]])
                wifi_RSSI_data.append(rssi_data_points[len_cmd])
                len_cmd += 1
            elif car_commands[i].startswith("B"):
                loc = move(loc, "B")
                RSSI_data_location.append([loc[1], loc[0]])
                wifi_RSSI_data.append(rssi_data_points[len_cmd])
                len_cmd += 1
            elif car_commands[i].startswith("L"):
                loc = move(loc, "L")
            elif car_commands[i].startswith("R"):
                loc = move(loc, "R")
        
        # if data_start == 0:
        #     RSSI_data_location = [sublist[::-1] for sublist in RSSI_data_location]
        # else:
        #     RSSI_data_location = RSSI_data_location[:data_start] + [sublist[::-1] for sublist in
        #                         RSSI_data_location[data_start:]]  # invert the x, y-axis to match with interpolation axis
        #     RSSI_data_location[data_start-1] = RSSI_data_location[data_start-1][::-1]
        data_start += len_cmd
        print("load finished with data_start on " + str(data_start))
    elif user_input == "limit":
        RSSI_LIMIT[0] = int(input("Enter the lower limit: "))
        RSSI_LIMIT[1] = int(input("Enter the upper limit: "))
    elif user_input == "clear" or user_input == "clr":
        wifi_RSSI_data = []
        RSSI_data_location = []
        wifi_RSSI_data = []
        data_start = 0
    elif user_input == "exit" or user_input == "quit" or user_input == "q":
        break
    elif user_input == "h" or user_input == "help":
        print('''
        return:             collect a new data point
        show:               show the current data points
        showL:              show the current locations
        -:                  remove the last data point
        +:                  add the last data point
        plot:               plot the heatmap
        plotD:              plot the heatmap with detailed floor map
        plotDI:             plot the heatmap with detailed floor map and interpolate the corners with RSSI_LIMIT[0]
        plotDE:             plot the heatmap with detailed floor map and extropolation
        save <filename>:    save the data points and the plot to a file
        start <locationX> <locationY> <direction>:    set the car starting location and direction
        load <car_commands>:    load car commands and retrieve the rssi data from the file
        limit:              set the RSSI limit
        clr/clear:          clear the data points and the plot
        q/quit/exit:        exit the program
        h/help:             show help message
        ''')
    else:
        print("Invalid command. Please enter a valid command.")

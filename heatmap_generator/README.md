# Heatmap Generate v2.0 Aug18
## Manually generate CIC Heatmap 
if using windows computer, rewrite the retrieved signal strength method at path lib.retrieve_signal_strength
\>python heatmap_generator_termianl_app*
To collect the data
\>[return] 
After collect 57 date point -- Plot it
# Heatmap Generate v1.0
## Manually with RSSI data
1. In heatmap_generate_by_huamn_walk.py TODO Section
    - Fill SSI_data_location with [x, y] location
    - Fill wifi_RSSI_data with corresponding RSSI data point
2. Run the program by >python heatmap_generate_by_huamn_walk.py
3. \>plotD to show the headmap 

### To see the extropolated heatmap
1. \> plotD
(hover the mouse to find the tx position)
3. \>q to exit the program and change the tx_loc to the right location
4. Re-run the program and >plotDE to show the heat map 
## Manually without RSSI data
For windows, rewrite the function getCurrentWifiSignalInfo to retrieved RSSI data from local computer
1. Fill RSSI_data_location with [x, y] location
1. Connect to the target WiFi
2. Run the program by >python heatmap_generate_by_huamn_walk.py
3. When walked on the corresponding location in sequence, hit return to read the RSSI data
4. \>plotD
## Using WiFi Car
1. Connect to the target WiFi
1. Find local computer IP address
1. Updata host to the IP address in file car_control/car_remote_control.py and update the IP address in Arduino code and then upload the Arduino code to WiFi car
2. Run >python car_control/car_remote_control.py
3. Turn on the WiFi car and wait until the command line saying "Please enter a command: " 
1. Calibrate the WiFi car to find the moving 1 meter distance and 90 degree turn
1. Approximate F2100 to move forward 1 meter and L800 to turn left 90 degree where F is forward, B is backward, L is left, R is right. The following number is the operating time in ms. 
1. Clean the data in the file data/rssi_data_car.txt
1. Run the command in car_remote_control terminal to control the car moving through the space (better to use command sequence split by space, for example >F2100 F2100 F2100 F2100 R700 F2100 F2100 F2100 F2100 L680 F2100 F2100 F2100 F2100 F2100 L680 F2100 F2100 F2100 F2100 F2100).
1. Set the tx_loc in file heatmap_generate_by_huamn_walk.py
1. Run >python heatmap_generate_by_huamn_walk.py
1. \>start car_start_position_x car_start_position_y heading_direction(0:up in floor plan, 1:right in floor plan, 2:down in floor plan, 3:left in floor plan)
1. \>load all the car control command after the data clean in the file data/rssi_data_car.txt, seperate by space
1. \>plotD OR >plotDE
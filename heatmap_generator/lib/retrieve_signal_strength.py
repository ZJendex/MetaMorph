import subprocess
import re
import time

'''
This function returns the current wifi signal strength in dBm

Caution: this function is only worked on macOS
'''
def getCurrentWifiSignalInfo(raw=False):
    # WifiSignalPlotter.main()
    result = subprocess.run(
        ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", '-I'],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # print(result.stdout.decode())
    result = result.stdout.decode()
    if raw:
        return result
    # Use a regular expression to get the first number
    match = re.findall(r'(-?\d+)', result)
    if match:
        return match[0]
    else:
        raise Exception("Error getting the RSSI Info")
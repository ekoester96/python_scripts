#!/usr/bin/env python3

# Author: Ethan
# Date Created: 5/6/2025
# Date Modified: 5/9/2025
# Description: Python script to change a MAC address using 'ip' and argparse
# Usage: sudo python3 ./mac_changer.py -i eth0

import subprocess
import argparse
import re
import random

# function that allows us to set arguments for the network interface to spoof our mac address
def get_arguments():
    parser = argparse.ArgumentParser(description="Change MAC address for a given network interface.")
    parser.add_argument("-i", "--interface", required=True, help="Network interface to change MAC address (e.g., eth0)")
    args = parser.parse_args()
    return args

# function that generates a random mac address
def random_mac():
    new_mac = [0x00, 0x50, 0x56, random.randint(0x00, 0x7f), random.randint(0x00, 0x7f), random.randint(0x00, 0x7f)]
    mac_address = ":".join(map(lambda x: "%02x" % x, new_mac))
    return mac_address

# function that runs the commands in linux to change the mac address to the randomly generated one
def change_mac(interface, mac_address):
    print(f"[+] Changing MAC address for {interface} to {mac_address}")
    subprocess.call(["ip", "link", "set", "dev", interface, "down"])
    subprocess.call(["ip", "link", "set", "dev", interface, "address", mac_address])
    subprocess.call(["ip", "link", "set", "dev", interface, "up"])

# current mac address for our interface
def get_current_mac(interface):
    ip_result = subprocess.check_output(["ip", "link", "show", interface]).decode("utf-8")
    mac_address_search_result = re.search(r"link/ether (\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)", ip_result)
    if mac_address_search_result:
        return mac_address_search_result.group(1)
    else:
        return None

# calling functions passing through parameters to change the mac address to the new randomly generated address
args = get_arguments()
new_mac = random_mac()

current_mac_before = get_current_mac(args.interface)
print(f"Current MAC address of {args.interface} is: {current_mac_before}")

change_mac(args.interface, new_mac)

current_mac_after = get_current_mac(args.interface)
if current_mac_after == new_mac:
        print(f"[+] MAC address was successfully changed to {new_mac}")
else:
        print(f"[-] MAC address change failed. Current MAC is {current_mac_after}")




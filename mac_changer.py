#!/usr/bin/env python

# Author: Ethan
# Date Created: 5/6/2025
# Date Modified: 5/8/2025
# Description: python script to change a mac address
# Usage: python3 ./mac_changer.py -i eth0 -m 00:11:22:33:44:55

# module that allows us to run bash commands from python
import subprocess
# module for parsing command line options
import optparse
# import regex module to search for characters in output
import re

# defining a new function that can be called in the program
def get_arguments():
    # variable/object that uses optparse module and the option parse function
    parser = optparse.OptionParser()
    # methods using the parser variable to add options that allows user to enter multiple options for the command line arguments
    parser.add_option("-i", "--interface", dest="interface", help="Interface to change mac address")
    parser.add_option("-m", "--mac", dest="new_mac", help="Input for new MAC address")
    # arguments to return when calling function
    (options, arguments) = parser.parse_args()
    # if statement to check for errors when entering interface and mac options
    if not options.interface:
        parser.error("[-] Please specify an interface, use --help for more info")
    elif not options.new_mac:
        parser.error("[-] Please specify a new MAC address, use --help for more info")
    # return options when function is successful
    return options

# function that uses bash to change MAC address
def change_mac(interface, new_mac):
    print("Changing MAC address for " + interface + " to " + new_mac)
    subprocess.call(["ifconfig", interface, "down"])
    subprocess.call(["ifconfig", interface, "hw", "ether", new_mac])
    subprocess.call(["ifconfig", interface, "up"])

def get_current_mac(interface):
    # use ifconfig to see result of changed mac address
    ifconfig_result = subprocess.check_output(["ifconfig", interface])
    # print just the mac address using regex to match MAC address pattern in the output of ifconfig_result
    mac_address_search_result = re.search(r"\w\w:\w\w:\w\w:\w\w:\w\w:\w\w", str(ifconfig_result))
    if mac_address_search_result:
        return mac_address_search_result.group(0)
    else:
        print("[-] Could not find any MAC address to change to")

# calling the get_arguments function, the user will determine the interface and new mac address
options = get_arguments()
# calling the function that uses the interface and mac address input by the user to change the mac address
change_mac(options.interface, options.new_mac)
# calling function that returns current mac address
current_mac = get_current_mac(options.interface)

# verify mac address has been changed
current_mac = get_current_mac(options.interface)
if current_mac == options.new_mac:
    print("MAC address was successfully changed to " + current_mac)
else:
    print("MAC address has not been changed")


# security hazard this way of executing bash in python allows users to input their own bash commands
# subprocess.call("ifconfig " + interface + " down", shell=True)
# subprocess.call("ifconfig " + interface + " hw ether " + new_mac, shell=True)
# subprocess.call("ifconfig " + interface + " up", shell=True)

# more secure way of using python that doesn't allow additional commands to be executed by the user input
# subprocess.call(["ifconfig", interface, "down"])
# subprocess.call(["ifconfig", interface, "hw", "ether", new_mac])
# subprocess.call(["ifconfig", interface, "up"])

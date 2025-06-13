#!/usr/bin/env python
# Author: Ethan
# Date: 6/13/2025
# Usage: python ./network_scanner.py -t <Example: 192.168.178.1/24>
# Definition: run the script using a local ip range to send arp packets to all ip addresses and return the MAC addresses 
#             of each assigned IP address. Each address found is stored in a dictionary list and printed in the terminal.

import optparse
import scapy.all as scapy

def get_arguments():
    parser = optparse.OptionParser()
    parser.add_option("-t", "--target", dest="target", type="string", help="Target IP / IP range")
    options, arguments = parser.parse_args()
    return options

def scan(ip):
    arp_request = scapy.ARP(pdst = ip)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast / arp_request
    answered_list = scapy.srp(arp_request_broadcast, timeout=1, verbose = False)[0]
    print("-"*60)

    clients_list = []
    for element in answered_list:
        client_dict = {"ip": element[0].psrc, "mac": element[1].hwsrc}
        clients_list.append(client_dict)

    return clients_list

def print_result(results_list):
    print("IP Address\t\tMAC Address\n")
    for client in results_list:
        print(client["ip"] + "\t\t" + client["mac"])

options = get_arguments()
scan_result = scan(options.target)
print_result(scan_result)

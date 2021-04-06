#!/usr/bin/env python3

import sys, re, json, asyncio
from argparse import ArgumentParser, Namespace
  
def mac_addr(x):
    if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", x.lower()):
        raise ValueError()
    return x

 
parser = ArgumentParser()
subparsers = parser.add_subparsers(help='action', dest='command', required=True)
 
sub = subparsers.add_parser('scan', help = "Scan for ThermoBeacon devices")
sub = subparsers.add_parser('identify', help = "Identify a device")
sub.add_argument('-mac', type=mac_addr, required=True)

'''
sub = subparsers.add_parser('add', help = "Add device")
sub.add_argument('-mac', type=mac_addr, required=True)
sub.add_argument('-name', default='no name')
sub = subparsers.add_parser('remove', help = "Remove device")
sub.add_argument('-mac', type=mac_addr, required=True)
sub = subparsers.add_parser('config', help = 'Save configuration')
sub.add_argument('-s', '--save', action='store_true', help='Save configuration to file')
sub = subparsers.add_parser('discover', help = "Listen for device")
sub.add_argument('-name', required=True, metavar='Name', help='Device Name')
sub.add_argument('-t', type=int, choices=range(10,31), default=10, metavar='Timeout', help='Seconds to wait')
'''


args = parser.parse_args()

print(args.command)



#!/usr/bin/env python3

import sys, re, json, asyncio
from argparse import ArgumentParser, Namespace

from bleak import BleakScanner
from tb_protocol import TBMsgAdvertise, TBMsgMinMax

  
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

#print(args.command)


def main():
    cmd = args.command
    if cmd=='scan':
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(scan())
        except KeyboardInterrupt:
            print()
            return

async def scan():
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
    await scanner.start()
    await asyncio.sleep(540)
    await scanner.stop()


def detection_callback(device, advertisement_data):
    #('RSSI:', -88, AdvertisementData(local_name='ThermoBeacon', manufacturer_data={16: b'\x00\x00\x17\x1a\x00\x00\xac\xfap\x01q\xc8\x01\x00X\x01\x84\x18\x08\x00'}, service_uuids=['0000fff0-0000-1000-8000-00805f9b34fb']))
    name = advertisement_data.local_name
    if name is None:
        return
    if name != 'ThermoBeacon':
        return
    msg = advertisement_data.manufacturer_data
    #print(bytes.fromhex(msg))
    
    #print(device.address, type(device))
    for key in msg.keys():
        #print(str(key) +' '+msg[key].hex())
        #bvalue=bytearray([key&0xff, (key>>8)&0xff]) + msg[key]
        bvalue = msg[key]
        #print(bvalue.hex())
        mac = device.address.lower()
        if len(bvalue)==18:
            data = TBMsgAdvertise(key, bvalue)
            #print(device.address, data.tmp, data.hum, data.upt)
            print('[{0}] [{6:02x}] T= {1:5.2f}\xb0C, H = {2:3.2f}%, Button:{4}, Battery : {5:02.0f}%, UpTime = {3:8.0f}s'.\
                  format(mac, data.tmp, data.hum, data.upt, 'On ' if data.btn else 'Off', data.btr, data.id))
        else:
            data = TBMsgMinMax(key, bvalue)
            print('[{0}] [{5:02x}] Max={1:5.2f}\xb0C at {2:.0f}s, Min={3:5.2f}\xb0C at {4:.0f}s'.\
                  format(mac, data.max, data.max_t, data.min, data.min_t, data.id))


if __name__ == '__main__':
    main()


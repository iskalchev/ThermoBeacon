#!/usr/bin/env python3

import sys, re, json, asyncio
from argparse import ArgumentParser, Namespace
import bleak

import paho.mqtt.client as mqtt
 

from bleak import BleakClient, BleakScanner
from tb_protocol import *

#Transmit Handle 0x0021
TX_CHAR_UUID = '0000fff5-0000-1000-8000-00805F9B34FB'
#Read Handle 0x0024
RX_CHAR_UUID = '0000fff3-0000-1000-8000-00805F9B34FB'

  
def mac_addr(x):
    if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", x.lower()):
        raise ValueError()
    return x


parser = ArgumentParser()
subparsers = parser.add_subparsers(help='action', dest='command', required=True)

sub = subparsers.add_parser('scan', help = "Scan for ThermoBeacon devices")
sub.add_argument('-mac', type=mac_addr, required=False)
sub.add_argument('-t', type=int, default = 20, metavar='<Scan duration, seconds>', required=False)
sub = subparsers.add_parser('identify', help = "Identify a device")
sub.add_argument('-mac', type=mac_addr, required=True)
sub = subparsers.add_parser('query', help = "Query device for details")
sub.add_argument('-mac', type=mac_addr, required=True)
sub = subparsers.add_parser('dump', help = "Dump logged data")
sub.add_argument('-mac', type=mac_addr, required=True)
sub = subparsers.add_parser('query', help = "Query device for details")
sub.add_argument('-mac', type=mac_addr, required=True)
sub.add_argument('-t', type=int, default = 3, metavar='<Query duration, seconds>', required=False)
sub = subparsers.add_parser('mqtt', help = "Send data via mqtt")
sub.add_argument('-mac', type=mac_addr, required=True)
sub.add_argument('-t', type=int, default = 3, metavar='<Query duration, seconds>', required=False)
sub.add_argument('-broker', required=True)
sub.add_argument('-port', type=int, required=True)
sub.add_argument('-topic', required=True)


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
    elif cmd=='identify':
        identify(args.mac)
        return
    elif cmd=='dump':
        dump(args.mac)
        return
    elif cmd=='query':
        Result = query(args.mac, args.t)                
        print(Result)
    elif cmd=='mqtt':
        send_mqtt(args.mac, args.t, args.broker, args.port, args.topic)
    else:
        print('Not yet implemented')


async def scan():
    scanner = BleakScanner()
    scanner.register_detection_callback(detection_callback)
    await scanner.start()
    await asyncio.sleep(540)
    await scanner.stop()


def detection_callback(device, advertisement_data):
    name = advertisement_data.local_name
    if name is None:
        return
    if name != 'ThermoBeacon':
        return
    msg = advertisement_data.manufacturer_data
    #print(device.rssi)
    for key in msg.keys():
        bvalue = msg[key]
        mac = device.address.lower()
        if len(bvalue)==18:
            data = TBAdvData(key, bvalue)
            print('[{0}] [{6:02x}] T= {1:5.2f}\xb0C, H = {2:3.2f}%, Button:{4}, Battery : {5:02.0f}%, UpTime = {3:8.0f}s'.\
                  format(mac, data.tmp, data.hum, data.upt, 'On ' if data.btn else 'Off', data.btr, data.id))
        else:
            data = TBAdvMinMax(key, bvalue)
            print('[{0}] [{5:02x}] Max={1:5.2f}\xb0C at {2:.0f}s, Min={3:5.2f}\xb0C at {4:.0f}s'.\
                  format(mac, data.max, data.max_t, data.min, data.min_t, data.id))


'''
'''
def dump(address):
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_dump(address))
    except bleak.exc.BleakDBusError as dber:
        print(dber.dbus_error)
    except Exception as exc:
        print('///'+str(exc))

async def _dump(address):
    client = BleakClient(address)
    try:
        await client.connect(timeout=10)
        print('connectd')
    except Exception as exc:
        print('exception ' + str(exc))
        return
    try:
        print(client.is_connected)

        cmd = TBCmdQuery()
        await client.write_gatt_char(TX_CHAR_UUID, cmd.get_msg())
        data = await client.read_gatt_char(RX_CHAR_UUID)
        resp = TBMsgQuery(data)
        print('01:'+data.hex())

        await client.start_notify(RX_CHAR_UUID, dump_callback)
        cmd_dump = bytes([TB_COMMAND_DUMP, 0, 0, resp.count&0xff, (resp.count>>8)&0xff, (resp.count>>16)&0xff, 1])
        cnt = 0
        while cnt<resp.count:
            c = 15 if resp.count-cnt>15 else resp.count-cnt
            cmd = TBCmdDump(cnt, c)
            cmd_dump = cmd.get_msg()
            cnt += c
            #print('cmd ', cmd_dump.hex())
            await client.write_gatt_char(TX_CHAR_UUID, cmd_dump)
        await asyncio.sleep(.5)
        data = await client.read_gatt_char(RX_CHAR_UUID)
        print(data.hex())
    finally:
        await client.disconnect()

def dump_callback(sender: int, data: bytearray):
    if data is None:
        return
    try:
        hdata = data.hex()
        msg = TBMsgDump(data)
        print(msg.offset, msg.count, msg.data)
        #print(f"{sender}: {hdata}")
    except Exception as exc:
        print(str(exc))

'''
'''
def identify(address):
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(_identify(address))
    except bleak.exc.BleakDBusError as dber:
        print(dber.dbus_error)
    except Exception as exc:
        print('///'+str(exc))

async def _identify(address):
    client = BleakClient(address)
    try:
        await client.connect(timeout=10)
        print('connectd')
    except Exception as exc:
        print('exception ' + str(exc))
        return

    try:
        cmd = TBCmdIdentify()
        await client.write_gatt_char(TX_CHAR_UUID, cmd.get_msg())
    finally:
        await client.disconnect()

'''
Thanks to Andreas Schmitz (Andy) two new commands implemented below: query, mqtt. 
The mqtt command queries the values and then publishes via mqtt
'''
def send_mqtt(SensorMac, SensorQueryDuration_s, broker, port, topic):
    Result = str(query(SensorMac, SensorQueryDuration_s))
    if len(Result) == 0:
        return		
    client = mqtt.Client()
    client.connect(host = broker, port = port)
    #FIXME add user, passwd
    client.loop_start()
    client.publish(topic = topic, payload = Result, qos = 1)
    client.disconnect()

'''
'''
def query(SensorMac, SensorQueryDuration_s):
	#Not sure how to return values from a BleakScanner::callback
	#function. Thus using global variables.
    global QueryResults
    QueryResults = dict()
    global TargetMac
    TargetMac = SensorMac
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(async_query(SensorQueryDuration_s))
    except KeyboardInterrupt:
        print()
        return
    return(QueryResults)


async def async_query(SensorQueryDuration_s):    
    scanner = BleakScanner(query_callback)
    await scanner.start()    
    await asyncio.sleep(SensorQueryDuration_s)  
    await scanner.stop()

def query_callback(device, advertisement_data):
    global QueryResults
    global TargetMac
    name = advertisement_data.local_name
    if name is None:
        return
    if name != 'ThermoBeacon':
        return
    msg = advertisement_data.manufacturer_data    
    for key in msg.keys():        
        bvalue = msg[key]
        mac = device.address.lower()
        if mac != TargetMac:
            continue
        if len(bvalue)==18:
            QueryResults.clear()
            data = TBAdvData(key, bvalue)
            QueryResults["mac"] = mac
            QueryResults["temp"] = round(float(data.tmp),2)
            QueryResults["relhum"] = round(float(data.hum),2)
            QueryResults["button"] = data.btn
            QueryResults["battery"] = round(float(data.btr),2)
            QueryResults["uptime"] = int(data.upt)
            QueryResults["mac"] = mac
        else:
            pass
			#This data contains min and max values - ignore.
            #data = TBAdvMinMax(key, bvalue)
            #print('[{0}] [{5:02x}] Max={1:5.2f}\xb0C at {2:.0f}s, Min={3:5.2f}\xb0C at {4:.0f}s'.\
            #      format(mac, data.max, data.max_t, data.min, data.min_t, data.id))


if __name__ == '__main__':
    main()


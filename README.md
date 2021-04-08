#  Bluetooth scanner for ThermoBeacon BLE devices.

## Prerequisites
### 1. This command line tool requires Python 3.7 or grter.
### 2. Install [bleak Python library](https://github.com/hbldh/bleak)
    $ sudo pip3 install bleak


## Usage
    usage: tbcmd.py [-h] {scan,identify,query,dump} ...
    
    positional arguments:
      {scan,identify,query,dump}
                        action
        scan                Scan for ThermoBeacon devices
        identify            Identify a device
        query               Query device for details
        dump                Dump logged data

    optional arguments:
      -h, --help            show this help message and exit


## Supported devices
[Brifit Bluetooth thermometer and hygrometer, wireless](https://www.amazon.de/-/en/gp/product/B08DLHFKT3/ref=ppx_yo_dt_b_asin_title_o00_s01?ie=UTF8&psc=1)

[ORIA Wireless Thermometer Hygrometer](https://www.amazon.co.uk/dp/B08GKB5D1M/ref=emc_b_5_t)

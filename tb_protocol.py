
'''
decode temperature value from byte(2) array
'''

def tb_decode_temperature(b:bytes) -> float:
    result = int.from_bytes(b, byteorder='little')/16.0
    if result>4000:
        result -= 4096
    return result

'''
decode humidity value from byte(2) array
'''

def tb_decode_humidity(b:bytes) -> float:
    result = int.from_bytes(b, byteorder='little')/16.0
    if result>4000:
        result -= 4096
    return result

'''
ADVERTISING MESSAGES

Decode Manufacturer specific data from BLE Advertising message

Message length: 20 bytes

bytes | content
========================================================
00-01 | code
02-02 | 00 ?
03-03 | 0x80 if Button is pressed else 00
04-09 | mac address
10-11 | battery level: seems that 3400 = 100% (3400 mV, not quite sure)
12-13 | temperature
14-15 | humidity
16-19 | uptime: seconds sinse the last reset
'''

MSG_ADVERTISE_DATA   = 1
MSG_ADVERTISE_MINMAX = 2

class TBAdvertisingMessage:
    def __init__(self, msg_type, id, bvalue):
        if id not in [0x10, 0x11]:
            raise ValueError()
        self.id = id
        self.msg_type = msg_type
        self.btn = False if bvalue[1]==0 else True
        self.mac = int.from_bytes(bvalue[2:8],byteorder='little')

class TBAdvData(TBAdvertisingMessage):
    def __init__(self, id, bvalue):
        TBAdvertisingMessage.__init__(self, MSG_ADVERTISE_DATA, id, bvalue)

        self.btr = int.from_bytes(bvalue[8:10],byteorder='little')
        self.btr = self.btr*100/3400
        self.tmp = tb_decode_temperature(bvalue[10:12])
        self.hum = tb_decode_humidity(bvalue[12:14])
        self.upt = int.from_bytes(bvalue[14:18],byteorder='little')


'''
Message length: 22 bytes

bytes | content
========================================================
00-01 | code
02-02 | 00 ?
03-03 | 0x80 if Button is pressed else 00
04-09 | mac address
10-11 | max temp
12-15 | max temp time (s)
16-17 | min temp
18-21 | min temp time (s)
'''

class TBAdvMinMax(TBAdvertisingMessage):
    def __init__(self, id, bvalue):
        TBAdvertisingMessage.__init__(self, MSG_ADVERTISE_MINMAX, id, bvalue)
        
        self.max = tb_decode_temperature(bvalue[8:10])
        self.max_t = int.from_bytes(bvalue[10:14],byteorder='little')
        self.min = tb_decode_temperature(bvalue[14:16])
        self.min_t = int.from_bytes(bvalue[16:20],byteorder='little')

'''
COMMANDS
 
'''
TB_COMMAND_QUERY      = 0x01
TB_COMMAND_RESET      = 0x02
TB_COMMAND_TEMP_SCALE = 0x03
TB_COMMAND_IDENTIFY   = 0x04
TB_COMMAND_DUMP       = 0x07


'''
'''

class TBMsgQuery:
    def __init__(self, bvalue):
        self.msg = bvalue[0]
        self.count = int.from_bytes(bvalue[1:3],byteorder='little')

'''
'''

class TBMsgDump:
    def __init__(self, bvalue):
        self.msg = bvalue[0]
        self.offset = int.from_bytes(bvalue[1:5], 'little')
        self.count = bvalue[5]
        self.data = []
        for c in range(self.count):
            t = tb_decode_temperature(bvalue[6+c*2:6+c*2+2])
            h = tb_decode_humidity(bvalue[2*self.count+6+c*2:2*self.count+6+c*2+2])
            self.data.append({'t':t, 'h':h})

'''
Commands
'''


class TBCmdBase:
    def __init__(self, cmd):
        self.cmd = cmd

    def get_msg(self):
        return bytes([self.cmd])+self.get_params()

    def get_params(self):
        return bytes()

class TBCmdIdentify(TBCmdBase):
    def __init__(self):
        TBCmdBase.__init__(self, TB_COMMAND_IDENTIFY)
   
class TBCmdQuery(TBCmdBase):
    def __init__(self):
        TBCmdBase.__init__(self, TB_COMMAND_QUERY)

class TBCmdDump(TBCmdBase):
    def __init__(self, start, count=15):
        TBCmdBase.__init__(self, TB_COMMAND_DUMP)
        self.offset = start
        self.count  = count

    def get_params(self):
        return self.offset.to_bytes(4,'little') + self.count.to_bytes(4,'little')

import sys
import os

if "../carla_simulator" not in sys.path:
    sys.path.append("../carla_simulator")

from can_utilities import *
import cantools
import can
import socket
import os
from can import Message
from config import *
from config_bb import *
import serial
import time
from can.interface import Bus
from timeit import default_timer as timer

# vengono lanciati gli script per configurare l'interfaccia CAN e l'access point
os.system('./can1init.sh')
os.system('./init_wlan0.sh')

db = cantools.database.load_file(db_name)

bb_pi_addr = (udp_ip_bb_pi, udp_port_bb_pi)
sock_pi = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock_pi.bind(bb_pi_addr)
sock_pi.settimeout(0.0001)


i = 0
flag = True
msg_rec = False
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
can_list = []
bus = Bus('can1', bustype='socketcan', fd=False)

print("While Loop")
# start_timer = timer()

while True:
    msg = bus.recv(timeout=0.001)
    
    if msg is not None:
        # msg.timestamp = timer() - start_timer
        print(msg)
    try:
        data = sock_pi.recv(2048)
    except KeyboardInterrupt:
        raise
    except:
        data = None

    if data is not None:
        can_list.append(decode_udp_msg(data.decode().split("*")))
        # print(data)
    for msg_pi in can_list:
        print("messaggio pi:" + str(msg_pi))
        bus.send(msg_pi)
    can_list = []
bus.shutdown()

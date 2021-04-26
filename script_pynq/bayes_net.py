
# coding: utf-8

# Prima di utilizzare l'interfaccia CAN sulla pynq è necessario caricare sull'FPGA *can.bit* che abilita il controller e assegna ai pin CAN_TX e CAN_RX i pin JB2_p e JB2_n sul PMODB. Tentare di utilizzare l'interfaccia CAN prima di far questo comporterebbe il blocco del controller (questo perchè di default sull'FPGA viene caricato *base.bit* in cui il controller CAN è disabilitato)

# In[1]:


from pynq import Overlay
import os
ol = Overlay("./can.bit")
# Abilito l'uso dell'interfaccia can su PmodB

os.system("ip link set can1 type can bitrate 500000")
os.system("ip link set can1 up")
# Configurata ed abilitata l'interfaccia can1


# In[1]:


import sys

if "../carla_simulator" not in sys.path:
    sys.path.append("../carla_simulator")
    
if "../ids" not in sys.path:
    sys.path.append("../ids")

import pomegranate
from bayesClasses import *
from idsClasses import *
import matplotlib.pyplot as plt
import numpy as np
import time
import can
from can_utilities import *
from config import *
import cantools
import serial
from can.interface import Bus
import math
import os.path
import timeit
from timeit import default_timer as timer


# Nella cella seguente viene definito l'ids a partire dal file *.xml* ottenuto grazie a weka

# In[2]:


name_file = "graph.xml"
bg = BayesGraph(name_file)
ids = IdsClassBayes(bg)


# In[3]:


print(bg.name_classes_nodes)
print(bg.parents)
# for node, cpt in bg.cpt_nodes.items():
#     print(node)
#     print(cpt)
print(bg.nodes_list)


# Nella cella seguente vengono recuperate le informazioni dai messaggi CAN ricevuti sul bus e viene richiamata la rete bayesiana. Inoltre vengono scritte in un file di log_result informazioni di interesse:
# * Numero della classificazione
# * Tempo in cui la rete bayesiana effettua la predizione
# * Stato dei parametri del veicolo
# * Risultato della predizione effettuata dalla rete
# * Se è in corso o meno un attacco al veicolo

# In[4]:


bus = Bus('can1',bustype='socketcan',fd=True)
db = cantools.database.load_file(db_name)
"""Abilitazione del bus per la ricezione"""

flag_calc_belief = False

if not os.path.isdir("log_result"):
    os.mkdir("log_result")
log_file_name = time.strftime("%d_%m_%y-%H_%M_%S.txt", time.localtime())
log_file_name = os.path.abspath(os.path.join("log_result", log_file_name))
log_file = open(log_file_name, "w")
# inizializzare con i nodi a partire dai quali calcolare la probabilità a posteriori
# se i nodi cambiano ad ogni ciclo reinizializzare la lista ad ogni ciclo
list_evidence_node = ['steer', 'abs_steer', 'throttle', 'speed', 'brake']
status_buf = StatusBuffer(bg.nodes_list)
msg_cont = 0

ids_msg = can.Message(arbitration_id=0, data=[255])
cont_bayes = 0 #numero di volte che viene richiamata la rete bayesiana
flag_16=0

attack_index = bg.nodes_list.index('attack')
try:
    while(True):
        msg = bus.recv()
        timestamp = msg.timestamp
        print(str(msg_cont) + str(msg), file=log_file)
        msg_cont += 1
        if msg.arbitration_id < 5:
            rec_msg = messageCodec(db, msg=msg).get_data()
            
            """Ricezione del messaggio"""
            if rec_msg[0] == db.get_message_by_name("Steer").frame_id:
                degree_read = (rec_msg[1]["Degree"] - num_section_steer)
                steer = degree_read / num_section_steer

            elif rec_msg[0] == db.get_message_by_name("Pedal").frame_id:
                throttle_read = (rec_msg[1]["Throttle"])
                brake_read = (rec_msg[1]["Brake"])
                throttle = (throttle_read / num_section_pedals)/2
                brake = (brake_read / num_section_pedals)/2
                
            elif rec_msg[0] == db.get_message_by_name("GearMsg").frame_id:
                gear = rec_msg[1]["Gear"]
                reverse = rec_msg[1]["Reverse"]
                reverse = bool(reverse)
                gear = gear - 1
                
            elif rec_msg[0] == db.get_message_by_name("Status").frame_id:
                speed = rec_msg[1]["Speed"]/max_speed_spedometer
                
                
                status_buf.add_status({'steer': steer, 'abs_steer':abs(steer), 'throttle': throttle,                                        'brake': brake, 'speed': speed}, timestamp)
                if flag_16==7:
                    flag_calc_belief = True
                    flag_16=0
                else:
                    flag_16+=1
            """Calcolo della probabilità a posteriori"""
            if flag_calc_belief:
                last_status = status_buf.get_last_status()
                dict_evidence = last_status.get_dict_by_keys(list_evidence_node)
                start = timer()
                pred, max_pred_class = ids.predict(dict_evidence)
                end = timer()
                print("classificazione numero: {}".format(cont_bayes), file=log_file)
                print("exec time: {}".format(end - start), file=log_file)
                print("status rete--------------------------", file=log_file)
                print(last_status, file=log_file)
                print("predizione---------------------------", file=log_file)
                print(pred[attack_index], file=log_file)
                if max_pred_class[attack_index] == '(0.5-inf)':
                    print("--------------attacco riconosciuto-------------")
                    print("--------------attacco riconosciuto-------------", file=log_file)
                    bus.send(ids_msg)
            
                flag_calc_belief = False
                cont_bayes += 1


finally:

    bus.shutdown()
    log_file.close()


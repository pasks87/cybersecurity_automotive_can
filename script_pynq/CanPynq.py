
# coding: utf-8

# Prima di utilizzare l'interfaccia CAN sulla pynq è necessario caricare sull'FPGA *can.bit* che abilita il controller e assegna ai pin CAN_TX e CAN_RX i pin JB2_p e JB2_n sul PMODB. Tentare di utilizzare l'interfaccia CAN prima di far questo comporterebbe il blocco del controller (questo perchè di default sull'FPGA viene caricato *base.bit* in cui il controller CAN è disabilitato)

# In[1]:


from pynq import Overlay
import os
ol = Overlay("./can.bit")
"""Abilitato l'uso dell'interfaccia can su PmodB"""

os.system("ip link set can1 type can bitrate 1000000")
os.system("ip link set can1 up")
"""Configurata ed abilitata l'interfaccia can1"""


# Nella seguente cella ogni messaggio letto sul bus viene stampato a video e scritto su un file di log_result

# In[ ]:


import can
import time
from can.interface import Bus

bus= Bus('can1',bustype='socketcan',fd=True)
"""Abilitazione del bus per la ricezione"""

nome = time.strftime("%d_%m_%y-%H_%M_%S.csv", time.localtime())
f = open(nome, "w")

while(True):
    msg = bus.recv()
    """Ricezione del messaggio"""
    print(msg)
    print(str(msg), file=f)
    """ Scrittura dei messaggi ricevuti in in file log_result.txt"""


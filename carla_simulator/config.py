#!/usr/bin/env python
"""
In questo file sono presenti tutti i parametri di configurazione necessari per avviare i vari script
"""
import os
import can

db_name = os.path.abspath('../carla_simulator/database_CAN/db_prova.dbc')
"""Percorso del database dei messaggi CAN"""

# CARLA_path = "C:\\Users\\netcom\\Desktop\\CARLA\\PythonAPI\\carla\\dist\\carla-*%d.%d-%s.egg"
# CARLA_path = "C:\\Users\\RESTAURO\\Desktop\\CARLA\\PythonAPI\\carla\\dist\\carla-*%d.%d-%s.egg"
CARLA_path = "D:\\Simone\\CARLA\\CARLA_win\\PythonAPI\\carla\\dist\\carla-*%d.%d-%s.egg"
"""Percorso del file .egg di CARLA"""

steer_idx = 0
"""Identificativo Volante"""

throttle_idx = 2
"""Identificativo Acceleratore"""

brake_idx = 3
"""Identificativo Freno"""

reverse_idx = 5
"""Identificativo Retromarcia"""

handbrake_idx = 4
"""Identificativo Freno a mano"""

num_section_steer = 128
"""
Numero di settori su cui viene effettuata la quantizzazione della posizione del volante.
I settori effettivi vanno da -num_section_steer a +num_section_steer.
"""

num_section_pedals = 64
"""
Numero di settori su cui viene effettuata la quantizzazione della pressione dei pedali.
I settori effettivi vanno da 0 a num_section_pedals.
"""

num_section_speedometer = 255
"""
Numero di settori su cui viene effettuata la quantizzazione per la lancetta del tachimetro
"""

max_speed_spedometer = 180
"""
Massima velocità indicabile dal tachimetro
"""

min_temp_engine = 273
"""
Temperatura minima che è possibile misurare con il sensore di temperatura posto nel liquido di raffreddamento
    a contato con il motore (in Kelvin)
"""

max_temp_engine = 433
"""
Temperatura massima che è possibile misurare con il sensore di temperatura posto nel liquido di raffreddamento
    a contato con il motore (in Kelvin)


"""

bit_temp_engine = 8
"""
Numero di bit usati per rappresentare la temperatura del motore
"""

min_rpm_engine = 750
"""
Minimo numero di giri raggiungibili dal motore
"""

max_rpm_engine = 5000
"""
Massimo numero di giri raggiungibili dal motore
"""

bit_rpm_engine = 8
"""
Numero di bit usati per rappresentare la temperatura del motore
"""

max_acceleration = 80
"""
Massima accelerazione del veicolo considerato (in m/s^2)
"""
#bus=Bus(channel="COM6",bitrate=1000000)
# udp_ip_bb = "127.0.0.1"
# udp_port_bb = 6001
# bb_addr = (udp_ip_bb, udp_port_bb)

# udp_ip_client = "127.0.0.1"
# udp_port_client = 6002
# client_addr = (udp_ip_client, udp_port_client)
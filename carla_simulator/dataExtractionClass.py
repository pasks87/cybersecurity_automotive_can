"""
In questo script sono implementati classi e motodi utili per recuperare informazioni sulla simulazione
che potranno essere analizzate in seguito
"""
from __future__ import print_function
import carla_simulator.config as config

import glob
import os
import sys
import time
import csv
from can_utilities import messageCodec
from config import *

try:
    sys.path.append(glob.glob(config.CARLA_path % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass


class DataExtractor():
    """
    In questa classe sono implementati metodi per estrarre, processare e memorizzare in un file di log_result dati di interesse
    ottenuti dalla simulazione.

    :param carla.world world: Oggetto in cui sono contenute tutte le informazioni riguardanti la simulazione
    :param cantools.database.can.database.Database db: Contiene tutte le informazioni presenti nel database di messaggi CAN
    :param stringa logs_dir: Path per la directory in cui inserire i messagg di log_result, di default viene creata la directory
           'logs' nella cartella corrente

    **Metodi:**
    """
    def __init__(self, world, db, logs_dir="logs"):
        self.name_file = time.strftime("%d_%m_%y-%H_%M_%S.csv", time.localtime())
        if not os.path.isdir(logs_dir):
            os.mkdir(logs_dir)
        self.name = os.path.abspath(os.path.join(logs_dir, self.name_file))

        self.world = world
        self.db = db

        self.fieldnames = ['timestamp', 'steer', 'swerve', 'throttle', 'brake', 'speed', 'acceleration', 'rpm', 'gear',
                           'latitude', 'longitude', 'cooling', 'Engine_temp', 'light', 'at_light',
                           'intensity_collision', 'actor_collision', 'crossed_lane', 'attack', 'recovery']

        self.dict_filenames = {}
        self.csv_file = open(self.name, 'w', newline='')
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fieldnames)
        self.csv_writer.delimiter = ','
        self.csv_writer.writeheader()

        self.timestamp_old = 0
        self.speed_old = 0

    def datacreator(self, timestamp, msg_list, monitor_param_sim):
        """
        Metodo per estrarre e scrivere i dati di interesse in un file di log_result in formato csv.

        :param timestamp: istante di tempo in cui vengono campionati i dati di interesse
        :type timestamp: float
        :param attack: ha valore '1' o '0' e indica rispettivamente la presenza o meno dell'attacco
        :type attack: int
        :param msg_list: lista di oggetti can.Message da cui estrarre le informazioni di interesse
        :type msg_list: lista
        :param monitor_param_sim: dizionario che contiene parametri calcolati nello script Simulatore.py
        :type monitor_param_sim: dizionario
        """
        # gear: marcia inserita(-1:retro, 0:folle, da 1 a 5 marce citroen)
        # rpm: numero di  giri del motore(intero da 750 a 4000)
        # throttle: posizione acceleratore(float da 0 a 1)
        # steer: posizione sterzo(float da - 1 a 1)
        # brake: posizione freno(float da 0 a 1)
        # acceleration: accellerazione(derivata velocità, float)
        # speed: velocità(float da 0 a 180)
        # swerve: sterzata(intero 0: sinistra, 1: destra)
        # attack(intero 0: no, 1: si)
        for msg in msg_list:
            rec_msg = messageCodec(self.db, msg=msg).get_data()

            if rec_msg[0] == self.db.get_message_by_name("Steer").frame_id:
                degree_read = (rec_msg[1]["Degree"] - num_section_steer)

                self.dict_filenames['steer'] = degree_read / num_section_steer

            elif rec_msg[0] == self.db.get_message_by_name("Pedal").frame_id:
                throttle_read = (rec_msg[1]["Throttle"])
                brake_read = (rec_msg[1]["Brake"])

                self.dict_filenames['throttle'] = (throttle_read / num_section_pedals) / 2
                self.dict_filenames['brake'] = (brake_read / num_section_pedals) / 2

            elif rec_msg[0] == self.db.get_message_by_name("Status").frame_id:
                speed = rec_msg[1]["Speed"]

                self.dict_filenames['speed'] = round(speed / config.max_speed_spedometer, 6)

        c = self.world.player.get_control()

        self.dict_filenames['swerve'] = 0 if self.dict_filenames['steer'] <= 0 else 1
        self.dict_filenames['gear'] = c.gear

        self.dict_filenames['light'] = self.world.player.get_traffic_light_state()
        self.dict_filenames['at_light'] = self.world.player.is_at_traffic_light()
        self.dict_filenames['timestamp'] = timestamp

        delta = timestamp - self.timestamp_old
        self.dict_filenames['acceleration'] = ((self.dict_filenames['speed'] - self.timestamp_old)/3.6)/(delta*1000.0)
        self.dict_filenames['acceleration'] = self.dict_filenames['acceleration'] / max_acceleration

        self.dict_filenames['rpm'] = monitor_param_sim['rpm']/max_rpm_engine

        self.dict_filenames['cooling'] = monitor_param_sim['Th_state']
        self.dict_filenames['Engine_temp'] = monitor_param_sim['T_engine'] / max_temp_engine

        self.dict_filenames['longitude'] = self.world.monitor_param['longitude']/180.0
        self.dict_filenames['latitude'] = self.world.monitor_param['latitude']/90.0

        self.dict_filenames['intensity_collision'] = self.world.monitor_param['intensity_collision']/50000
        self.dict_filenames['actor_collision'] = self.world.monitor_param['actor_collision']
        self.dict_filenames['crossed_lane'] = self.world.monitor_param['crossed_lane']

        self.dict_filenames['recovery'] = 1 if monitor_param_sim['recovery'] else 0
        self.dict_filenames['attack'] = monitor_param_sim['attack']

        self.csv_writer.writerow(self.dict_filenames)

        self.timestamp_old = timestamp
        self.speed_old = self.dict_filenames['speed']

    def close(self):
        """
        Metodo per chiudere il file di log_result
        """
        self.csv_file.close()

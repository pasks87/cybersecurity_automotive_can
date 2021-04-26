#!/usr/bin/env python

from __future__ import print_function
import can
import cantools
import math
import numpy as np
import socket

import pygame
from pygame.locals import KMOD_CTRL
from pygame.locals import KMOD_SHIFT
from pygame.locals import K_0
from pygame.locals import K_9
from pygame.locals import K_BACKQUOTE
from pygame.locals import K_BACKSPACE
from pygame.locals import K_COMMA
from pygame.locals import K_DOWN
from pygame.locals import K_ESCAPE
from pygame.locals import K_F1
from pygame.locals import K_LEFT
from pygame.locals import K_PERIOD
from pygame.locals import K_RIGHT
from pygame.locals import K_SLASH
from pygame.locals import K_SPACE
from pygame.locals import K_TAB
from pygame.locals import K_UP
from pygame.locals import K_a
from pygame.locals import K_c
from pygame.locals import K_d
from pygame.locals import K_h
from pygame.locals import K_m
from pygame.locals import K_p
from pygame.locals import K_q
from pygame.locals import K_r
from pygame.locals import K_s
from pygame.locals import K_w
from pygame.locals import K_MINUS
from pygame.locals import K_EQUALS

from can_utilities import *

from config import *

class EcuClass():
    """
    | Questa classe serve a modellare il funzionamento di una ECU.
    | Tale funzionameto è suddiviso in:

    1. Inizializzazione (metodo ``__init__()``): da effettuarsi quando viene istanziato l'oggetto appartenente a questa classe;
    2. Parsing degli eventi (metodo ``parse_events()``): vengono letti gli eventi di pygame e gli input dai vari joystick;
    3. Esecuzione dell'applicazione (metodo ``application()``): viene eseguita la specifica applicazione dell'ECU;
    4. Creazione dei messaggi (metodo ``create_message()``): vengono creati i messaggi in un determinato formato a partire
       dai risultati dell'applicazione.

    | I passi 2,3,4 vegono eseguiti in sequenza dal metodo ``run()`` che restituisce la lista dei messaggi generati.
    | Le varie ECU che fanno parte del veicolo sono sottoclassi di EcuClass.

    :param pygame.time.Clock clock: L'oggetto Clock è ottenuto richimando la funzione ``pygame.time.Clock()`` ed è
        usato per gestire la temporizzazione lato client
    :param cantools.database.can.database.Database db: Contiene tutte le informazioni presenti nel database di messaggi CAN

    **Metodi:**
    """
    def __init__(self, clock, db):
        """
        Inizializzazione  dell'ECU.

        :param Clock clock: l'oggetto Clock è ottenuto richimando la funzione ``pygame.time.Clock()`` e serve a tener
               traccia del tempo trascorso durante la simulazione
        :param cantools.database.can.database.Database db: Contiene tutte le informazioni presenti nel database di messaggi CAN
        """
        self.clock = clock
        self.db = db

    def parse_events(self, keys):
        """
        Parsing degli eventi di interesse e lettura degli input.

        :param lista keys: è una lista di booleani rappresentanti lo stato di ogni bottone sulla tastiera e sul joystick,
                tale lista è ottenuta richiamando la funzione ``pygame.key.get_pressed()``
        """
        pass

    def application(self):
        """
        Manipolazione degli input e creazione dei dati da inviare.
        """
        pass

    def create_message(self):
        """
        Crea messaggi in un formato specifico e restituisce la lista dei messaggi prodotti.

        :return: lista dei messaggi prodotti
        :rtype: lista
        """
        pass

    def run(self, keys):
        """
        Esegue in sequenza parse_evets, application e create_message e restituisce la lista di messaggi prodotti dall'ECU.

        :param lista keys: è una lista di booleani rappresentanti lo stato di ogni bottone sulla tastiera e sul joystick,
                tale lista è ottenuta richiamando la funzione ``pygame.key.get_pressed()``

        :return: (lista) lista dei messaggi prodotti
        """
        self.parse_events(keys)
        self.application()

        return self.create_message()


class EcuClassSteer(EcuClass):
    """
    ECU che gestisce lo sterzo.
    """
    def __init__(self, clock, db):
        super().__init__(clock, db)

        self.dict_events = {}
        self.sections_steer = []
        self.steerint = 0
        self.steerint_old = 0
        self.steer_cache = 0

        for i in range(-num_section_steer, num_section_steer + 1):
            self.sections_steer.append(i / num_section_steer)

        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            if ((pygame.joystick.get_count() > 0) and (
                    self.joystick.get_name() == "Logitech G29 Driving Force Racing Wheel USB")):
                self._steer_idx = steer_idx

            elif (pygame.joystick.get_count() > 0) and (self.joystick.get_name() == "Wireless Controller"):
                self._steer_idx = 2

    def parse_events(self, keys):

        if (pygame.joystick.get_count() > 0):
            self.dict_events["steerCmd"] = (self.joystick.get_axis(self._steer_idx))

        else:
            steer_increment = 5e-4 * self.clock.get_time()
            if keys[K_LEFT] or keys[K_a]:
                self.steer_cache -= steer_increment
            elif keys[K_RIGHT] or keys[K_d]:
                self.steer_cache += steer_increment
            else:
                self.steer_cache = 0.0

            self.steer_cache = min(1, max(-1, self.steer_cache))
            self.dict_events["steerCmd"] = round(self.steer_cache, 1)

    def application(self):
        degree_temp = 0
        death_zone = 0.03

        # viene effettuato il confronto tra i valori di index ed le sezioni precedentemente definite
        for section in self.sections_steer:
            if (section <= self.dict_events["steerCmd"]) and (
                    section + (1 / num_section_steer) > self.dict_events["steerCmd"]):
                degree_temp = section

        if (degree_temp < death_zone and degree_temp > -death_zone):
            degree_temp = 0.0

        if self.dict_events["steerCmd"] > 0.99:
            degree_temp = 0.99

        self.steerint = int(degree_temp * num_section_steer) + num_section_steer

    def create_message(self):
        can_msg_list = []
        # Se il messaggio è diverso dal precedente viene inviato un messaggio
        if (self.steerint != self.steerint_old):
            # Viene creato un messaggio con il nome precedentemente definito, poi viene inserito il contenuto tramite i metodi della
            # classe messageCodec definita nella libreria can_utilities
            msg_name = 'Steer'
            msg = messageCodec(self.db, msg_name=msg_name)
            data_steer = {'Degree': self.steerint}
            data_msg = msg.create_data(data_steer)
            can_msg = msg.create_msg(data_msg)
            # Il messaggio così generato viene inserito nella lista can_msg_list
            can_msg_list.append(can_msg)
            self.steerint_old = self.steerint

        return can_msg_list


class EcuClassPedals(EcuClass):
    """
    ECU che gestisce la pedaliera.
    """
    def __init__(self, clock, db):
        """
        Inizializzazione  dell'ECU
        """
        super().__init__(clock, db)
        self.dict_events = {}
        self.sections_pedals = []
        self.control_throttle = 0
        self.control_brake = 0
        self.control_throttle_old = 0
        self.control_brake_old = 0

        for j in range(-num_section_pedals, num_section_pedals + 1):
            self.sections_pedals.append(j / num_section_pedals)

        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            if ((pygame.joystick.get_count() > 0) and (
                    self.joystick.get_name() == "Logitech G29 Driving Force Racing Wheel USB")):
                self._throttle_idx = 2
                self._brake_idx = 3

            elif ((pygame.joystick.get_count() > 0) and (self.joystick.get_name() == "Wireless Controller")):
                self._throttle_idx = 4
                self._brake_idx = 5

    def parse_events(self, keys):
        """
        Parsing degli eventi di interesse e lettura degli input
        :return:
        """
        if (pygame.joystick.get_count() > 0):
            self.dict_events["throttleCmd"] = -self.joystick.get_axis(self._throttle_idx)
            self.dict_events["brakeCmd"] = -self.joystick.get_axis(self._brake_idx)

        else:
            self.dict_events["throttleCmd"] = 1.0 if keys[K_UP] or keys[K_w] else -1.0
            self.dict_events["brakeCmd"] = 1.0 if keys[K_DOWN] or keys[K_s] else -1.0

    def application(self):
        """
        Manipolazione degli input e creazione dei dati da inviare
        :return:
        """
        throttle_temp = 0
        brake_temp = 0

        for section in self.sections_pedals:
            if (section <= self.dict_events["throttleCmd"]) and (
                    (section + (1 / num_section_pedals)) > self.dict_events["throttleCmd"]):
                throttle_temp = section
        if self.dict_events["throttleCmd"] >= 1:
            throttle_temp = 1
        self.control_throttle = int(throttle_temp * num_section_pedals) + num_section_pedals

        for section in self.sections_pedals:
            if (section <= self.dict_events["brakeCmd"]) and (
                    section + (1 / num_section_pedals) > self.dict_events["brakeCmd"]):
                brake_temp = section

        if self.dict_events["brakeCmd"] >= 1:
            brake_temp = 1
        self.control_brake = int(brake_temp * num_section_pedals) + num_section_pedals

    def create_message(self):
        """
        Creazione del messaggio da inviare nel formato specificato e restituisce la lista dei messaggi prodotti
        :return: lista
        """
        can_msg_list = []

        if self.control_throttle != self.control_throttle_old or self.control_brake != self.control_brake_old:
            msg_name = 'Pedal'
            msg = messageCodec(self.db, msg_name=msg_name)
            data_throttle = {'Throttle': self.control_throttle, 'Brake': self.control_brake}
            data_msg = msg.create_data(data_throttle)
            can_msg = msg.create_msg(data_msg)

            can_msg_list.append(can_msg)

            self.control_throttle_old = self.control_throttle
            self.control_brake_old = self.control_brake
        return can_msg_list


class EcuClassVehicleInfo(EcuClass):
    """
    ECU che gestisce il cambio e recupera varie informazioni sullo stato del veicolo.
    """
    def __init__(self, clock, db, world, physics):
        super().__init__(clock, db)
        self.world = world
        self.physics = physics
        self.player_speed = self.world.player.get_velocity()
        self.player_control = self.world.player.get_control()

        self.speedometer_delta = max_speed_spedometer / num_section_speedometer
        self.speed = 0.0
        self.speed_old = 0.0

        self.reverse = 0
        self.reverse_old = 0
        self.gear = 0
        self.gear_old = 0

        self.lane_invaded = 0
        self.lane_invaded_old = 0

        self.T_engine = 0
        self.T_engine_old = 0
        self.interval_T_engine = (max_temp_engine - min_temp_engine)/pow(2,bit_temp_engine)

        self.Th_state = 0
        self.Th_state_old = 0

        self.rpm = 0
        self.rpm_old = 0
        self.interval_rpm = (max_rpm_engine - min_rpm_engine) / pow(2, bit_rpm_engine)

        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            if ((pygame.joystick.get_count() > 0) and (
                    self.joystick.get_name() == "Logitech G29 Driving Force Racing Wheel USB")):
                self._reverse_idx = 4

            elif ((pygame.joystick.get_count() > 0) and (self.joystick.get_name() == "Wireless Controller")):
                self._reverse_idx = 2

    def parse_events(self, keys):

        self.player_control = self.world.player.get_control()

        #Controllo sul cambio
        # TODO implementare retromarcia sia con q sia con cambio sequenziale
        if pygame.joystick.get_count() > 0:
            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN and event.button == self._reverse_idx:
                    self.reverse = 0 if self.reverse else 1
                elif event.type == pygame.KEYUP and event.key == K_c:
                    self.Th_state = 1 if self.Th_state == 0 else 0
                else:
                    pygame.event.post(event)
        else:
            for event in pygame.event.get():
                if event.type == pygame.KEYUP and event.key == K_q:
                    self.reverse = 0 if self.reverse else 1
                    # self.control.gear = 1 if self.control.reverse else -1
                elif event.type == pygame.KEYUP and self.player_control.manual_gear_shift and event.key == K_COMMA:
                    self.gear = max(0, self.gear - 1)
                    # self.control.gear = max(-1, self.control.gear - 1)
                elif event.type == pygame.KEYUP and self.player_control.manual_gear_shift and event.key == K_PERIOD:
                    self.gear = self.gear + 1
                    # self.control.gear = self.control.gear + 1
                elif event.type == pygame.KEYUP and event.key == K_c:
                    self.Th_state = 1 if self.Th_state == 0 else 0
                else:
                    pygame.event.post(event)

        # Controllo sul sensore di invasione di linea
        # TODO implementare il fatto che nel messaggio CAN deve dire anche il tipo di linea superata
        self.lane_invaded = self.world.lane_invasion_sensor.lane_invaded

    def application(self):
        self.player_speed = self.world.player.get_velocity()
        speed_tmp = 3.6 * math.sqrt(self.player_speed.x ** 2 + self.player_speed.y ** 2 + self.player_speed.z ** 2)

        self.speed = int(speed_tmp / self.speedometer_delta)

        # print("speed: {}".format(self.speed * self.speedometer_delta))

        if not self.player_control.manual_gear_shift:
            self.gear = max(self.player_control.gear, 0) + 1

        if self.reverse:
            self.gear = 0

        # Temperatura e stato termostato
        self.T_engine = int((self.physics["T_engine"] - min_temp_engine)/self.interval_T_engine)
        # self.Th_state = 0

        # RPM motore
        # print(self.rpm)
        self.rpm = max(0, int((self.physics["rpm"] - min_rpm_engine)/self.interval_rpm))

    def create_message(self):

        can_msg_list = []

        if self.reverse != self.reverse_old or self.gear != self.gear_old:
            msg_name = 'GearMsg'
            msg = messageCodec(self.db, msg_name=msg_name)
            data_gear = {'Gear': self.gear, 'Reverse': self.reverse}
            data_msg = msg.create_data(data_gear)
            can_msg = msg.create_msg(data_msg)

            can_msg_list.append(can_msg)

            self.reverse_old = self.reverse
            self.gear_old = self.gear

        if self.speed != self.speed_old or self.T_engine != self.T_engine_old or self.rpm != self.rpm_old:

            msg_name = 'Status'
            msg = messageCodec(self.db, msg_name=msg_name)
            data_status = {'Speed': self.speed, 'T_engine': self.T_engine, 'rpm_engine': self.rpm}
            # print("T engine: {}, value: {}".format(self.T_engine, self.physics['T_engine']))
            # print("Th_state: {}".format(self.Th_state))
            # print("rpm_engine: {}, value: {}".format(self.rpm, self.physics["rpm"]))
            # print("Speed: {}".format(self.speed))
            data_msg = msg.create_data(data_status)
            # print("data_staus:{}".format(data_msg))
            can_msg = msg.create_msg(data_msg)

            can_msg_list.append(can_msg)

            self.speed_old = self.speed
            self.T_engine_old = self.T_engine
            self.rpm_old = self.rpm

        if self.Th_state != self.Th_state_old:
            msg_name = 'Control_msg'
            msg = messageCodec(self.db, msg_name=msg_name)
            data_control = {'Th_state': self.Th_state}
            data_msg = msg.create_data(data_control)
            can_msg = msg.create_msg(data_msg)

            can_msg_list.append(can_msg)

            self.Th_state_old = self.Th_state

        return can_msg_list







0
    
    
    
    
#!/usr/bin/env python
"""
In questo script viene avviato il cient di CARLA
"""

from __future__ import print_function
import config

import glob
import os
import sys

try:
    sys.path.append(glob.glob(config.CARLA_path % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import can
import cantools
import carla
from carla import ColorConverter as cc
import argparse
import collections
import datetime
import logging
import math
import random
import re
import weakref
import serial
import timeit
import csv
from Carla_Classes import *
from dataExtractionClass import *
from EcuClass import *
from can.interfaces.seeedstudio import SeeedBus as Bus
from physicsModel import EngineSubModel
from physicsModel import TempSubModel

try:
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
    from pygame.time import get_ticks as milliseconds
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')


def game_loop(args):
    """Funzione che gestisce il loop di gioco"""
    # inizializza pygame
    pygame.init()
    pygame.font.init()

    world = None

    db = cantools.database.load_file(config.db_name)

    if args.can:
        bus = Bus("COM6", bitrate=500000)

        reader = can.BufferedReader()
        listener = [reader]
        notifier = can.Notifier(bus, listener)

    msg_new = None

    # istanziare ECU definite in EcuClass e aggiungerle alla lista
    ecu_list = []

    try:
        # collegamento con il server ed inizializzazione delle varie classi di controllo
        client = carla.Client(args.host, args.port)
        client.set_timeout(2.0)

        # display = pygame.display.set_mode((args.width, args.height), \
        #                                pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN)

        display = pygame.display.set_mode((args.width, args.height), pygame.HWSURFACE | pygame.DOUBLEBUF)

        hud = HUD(args.width, args.height)
        hud_par = {} #parametri il cui valore deve essere visualizzato nell'HUD
        monitor_param_sim = {} #parametri da monitore calcolati nello script Simulatore.py
        spawn_point = None

        if args.xlocation != 0.0 or args.ylocation != 0.0:
            location = carla.Location(x=float(args.xlocation), y=float(args.ylocation), z=2.0)
            spawn_point = carla.Transform(location, carla.Rotation(yaw=float(args.yaw)))

        world = World(client.get_world(), hud, args.filter, spawn_point)
        hud.set_waypoint(world)
        controller = DualControl(world, args.autopilot, db)
        clock = pygame.time.Clock()
        recovery = False

        # -----------------------------------------------
        # Definizioni modelli fisici del simulatore
        # -----------------------------------------------
        physics = {"Th_state": True}
        sm_engine = EngineSubModel()
        sm_t_engine = TempSubModel()
        hud_par['rpm'] = ['rpm: %f', sm_engine.N_engine]
        hud_par['T_engine'] = ['T_engine: %f', sm_t_engine.T_engine]

        # -----------------------------------------------
        # Definizioni ECU simulate
        # -----------------------------------------------
        ecu_list.append(EcuClassSteer(clock, db))
        ecu_list.append(EcuClassPedals(clock, db))
        ecu_list.append(EcuClassVehicleInfo(clock, db, world, physics))

        log_file = None
        if args.log:
            log_file = DataExtractor(world, db)

        msg_list = []
        msg_steer = can.Message(arbitration_id=0x1, data=[128])
        msg_pedal = can.Message(arbitration_id=0x2, data=[0])
        msg_rev = can.Message(arbitration_id=0x3, data=[0])
        msg_speed = can.Message(arbitration_id=0x4, data=[0])
        msg_control = can.Message(arbitration_id=0x5, data=[0])

        msg_list.append(msg_steer)
        msg_list.append(msg_pedal)
        msg_list.append(msg_rev)
        msg_list.append(msg_speed)
        msg_list.append(msg_control)

        msg_list_old = msg_list.copy()
        attack = 0
        attack2 = 0
        start_attack = 0
        stop_attack = 0
        nome = time.strftime("%d_%m_%y-%H_%M_%S.csv", time.localtime())
        if not os.path.isdir("atk_logs"):
            os.mkdir("atk_logs")
        atk_log = open(os.path.abspath(os.path.join("atk_logs", nome)), "w")
        i = 1
        num_msg = 0

        while True:
            ecu_data = []
            if args.can:
                msg_new = reader.get_message(timeout=0.01)

            msg_list_old = msg_list.copy()
            if msg_new != None: #sono stati ricevuti messaggi tramite la beaglebone
                print("msg_new: {}".format(msg_new))
                if msg_new.arbitration_id == 0:

                    stop_attack = milliseconds()
                    #attack2 indica la presenza(1) o meno(0) di un rilevamento
                    if attack2 == 0:
                        print("attacco, latenza:{}".format(stop_attack - start_attack))
                        print("{}\t\t1".format(i), file=atk_log)

                        attack2 = 1
                else:
                    #attack indica la presenza(1) o meno(0) di un attacco
                    if attack == 0:
                        print("inizio attacco")
                        attack = 1
                        start_attack = milliseconds()
                        print("{}\t1\t".format(i), file=atk_log)

            keys = pygame.key.get_pressed()
            #-----------------------------------------------
            # Update modelli fisici
            # -----------------------------------------------
            v = world.player.get_velocity()
            c = world.player.get_control()
            speed = 3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)
            gear = c.gear
            throttle = c.throttle * 100.0
            sm_engine.update(speed, gear, throttle)
            sm_t_engine.update(speed, physics["Th_state"], milliseconds())

            physics["rpm"] = sm_engine.N_engine
            physics["T_engine"] = sm_t_engine.T_engine

            monitor_param_sim["rpm"] = physics["rpm"]
            monitor_param_sim["T_engine"] = physics["T_engine"]

            hud_par['rpm'] = ['rpm: %f', sm_engine.N_engine]
            hud_par['T_engine'] = ['T_engine: %f', sm_t_engine.T_engine]

            # -----------------------------------------------
            # Calcolo applicazioni ECU
            # -----------------------------------------------
            for ecu in ecu_list:
                ecu_data += ecu.run(keys)

            msg_timestamp = milliseconds()

            # for msg in ecu_data:
            #     msg.timestamp = msg_timestamp
            #     print(msg)

            for elem in msg_list:
                for x in ecu_data:
                    if elem.arbitration_id == x.arbitration_id and elem.data != x.data:
                        msg_list[msg_list.index(elem)] = x

            if msg_list != msg_list_old:
                for elem in msg_list:
                    if args.can:
                        bus.send(elem)
                    num_msg += 1
                    if num_msg == 31:
                        if attack == 0 and attack2 == 0:
                            print("\t\t\t1", file=atk_log)
                        num_msg = 0

            if attack == 1:
                for elem in msg_list:
                    if msg_new is not None and msg_new.arbitration_id != 0:
                        if elem.arbitration_id == msg_new.arbitration_id:
                            msg_list[msg_list.index(elem)] = msg_new

            for event in pygame.event.get():
                if event.type == pygame.JOYBUTTONDOWN and event.button == 10:
                    attack = 0
                    attack2 = 0
                    recovery = False
                    i += 1
                    print("fine attacco")
                elif event.type == pygame.JOYBUTTONDOWN and event.button == 7:
                    recovery = False if recovery else True
                else:
                    pygame.event.post(event)

            if controller.parse_events(world, clock, msg_list, physics):
                return True


            # Vengono generate le immagini ad ogni tick
            world.tick(clock)
            hud_par['attack'] = ['attacco: %d', attack]
            hud_par['attack2'] = ['Rilevamento: %d', attack2]
            world.render(display, hud_par)

            monitor_param_sim["Th_state"] = physics["Th_state"]
            monitor_param_sim["attack"] = attack
            monitor_param_sim["recovery"] = recovery
            if args.log:
                log_file.datacreator(milliseconds(), msg_list, monitor_param_sim)

            pygame.display.flip()

            msg_new = None
            clock.tick_busy_loop(30)

    finally:

        if args.can:
            notifier.stop()
            bus.shutdown()

        if world is not None:
            world.destroy()

        pygame.quit()
        if log_file is not None:
            log_file.close()


def return_argparser():
    argparser = argparse.ArgumentParser()

    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='1280x720',
        help='window resolution (default: 1280x720)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.citroen.c3',
        help='actor filter (default: "vehicle.citroen.c3")')
    argparser.add_argument(
        '--xlocation',
        default=0.0,
        help='x location')
    argparser.add_argument(
        '--ylocation',
        default=0.0,
        help='y location')
    argparser.add_argument(
        '--yaw',
        default=0.0,
        help='yaw')
    argparser.add_argument(
        '-l', '--log',
        action='store_true',
        help='enable log_result')
    argparser.add_argument(
        '-c', '--can',
        default=False,
        action='store_true',
        help='enable CAN-Bus simulation')

    return argparser


def main():
    argparser = return_argparser()
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    try:
        game_loop(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')


if __name__ == '__main__':
    main()

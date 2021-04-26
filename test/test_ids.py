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
import math
import os.path
import timeit
from timeit import default_timer as timer
import re
import csv

#----------------------------------------------------
# Selezione della rete bayesiana da utilizzare
#----------------------------------------------------

name_file = "rete_prova.xml"
name_file = os.path.abspath(os.path.join("..\script_pynq", name_file))

#----------------------------------------------------
# Creazione della rete bayesiana, dell'ids, del buffer, del database di messaggi CAN,
#----------------------------------------------------
bg = BayesGraph(name_file)
ids = IdsClassBayes(bg)
status_buf = StatusBuffer(bg.nodes_list)
db = cantools.database.load_file(db_name)
#----------------------------------------------------
# Creazione dei file in cui scrivere i risultati
#----------------------------------------------------
log_file_name = time.strftime("%d_%m_%y-%H_%M_%S.txt", time.localtime())
log_file_name = os.path.abspath(os.path.join("log_result", log_file_name))
log_file = open(log_file_name, "w")

summary_file_name = summary_file_name = time.strftime("summary_%d_%m_%y-%H_%M_%S.txt", time.localtime())
summary_file_name = os.path.abspath(os.path.join("log_result", summary_file_name))
summary_file = open(summary_file_name , "w")

#----------------------------------------------------
# Lista contenente i nomi dei nodi da fornire come evidenza
#----------------------------------------------------
list_evidence_node = ['gear', 'rpm', 'throttle', 'steer', 'brake', 'acceleration', 'speed', 'swerve']

#----------------------------------------------------
# Inizializzazione di alcune variabili utili
#----------------------------------------------------
msg_cont = 0
flag_calc_belief = False

# numero di volte che viene richiamata la rete bayesiana
cont_bayes = 0
flag_16 = 0

max_rpm = 5000
min_rpm = 750
interval_rpm = (max_rpm - min_rpm)/pow(2,8)

max_T_engine = 423 # (150 gradi celsius)
min_T_engine = 273 # (0 gradi celsius)
interval_T_engine = (max_T_engine - min_T_engine)/pow(2,8)

attack_index = bg.nodes_list.index('attack')

steer = 0
throttle = 0
brake = 0
gear = 0
speed = 0
speed_old = 0
timestamp_old = 0
rpm = 0
th_state = False
swerve = 0
T_engine = min_T_engine
acceleration = 0

exec_time_list = []
# lunghezza pari al numero delle classificazione, 0:attacco non rilevata 1:attacco rilevato
rel_atk_list = []

first_timestamp = 0.0

#----------------------------------------------------
# Lettura e decodifica dei messaggi CAN e applicazione della rete bayesiana
#----------------------------------------------------
try:
    # ----------------------------------------------------
    # Apertura dei file che contengono i messaggi CAN
    # ----------------------------------------------------
    for elem in os.listdir(".\\can_bus"):

        csv_first_time = 0
        csv_last_time = 0

        status_buf = StatusBuffer(bg.nodes_list)
        msg_cont = 0
        flag_calc_belief = False

        cont_bayes = 0  # numero di volte che viene richiamata la rete bayesiana
        flag_16 = 0

        steer = 0
        throttle = 0
        brake = 0
        gear = 0
        speed = 0
        speed_old = 0
        timestamp_old = 0
        rpm = 0
        th_state = False
        swerve = 0
        T_engine = min_T_engine
        acceleration = 0

        # in questo caso ogni file di log contiene un solo attacco e il nome del file corrisponde al nome dell'attacco
        atk_type = elem[0:-4]
        name_csv = elem[0:-3] + "csv"
        rel_atk_list = []

        if name_csv in os.listdir(".\\log_csv"):
            reader_csv = csv.reader(open(".\\log_csv\\" + name_csv), delimiter=',')

            for row in reader_csv:
                if row[0] != 'timestamp' and csv_first_time == 0:
                    csv_first_time = float(row[0])
                if row[11] == '1' and csv_last_time == 0:
                    csv_last_time = float(row[0])

        reader = open(".\\can_bus\\" + elem, 'r')
        print("", file=log_file)
        print("Tipologia di attacco: {}".format(atk_type), file=log_file)
        print("", file=log_file)

        # ----------------------------------------------------
        # Decodifica dei messaggi CAN del file di log
        # ----------------------------------------------------
        for row in reader:
            msg = can.Message()
            row_split = row.split("    ")
            # print("row:{}:".format(row))
            for elem in row_split:
                if 'Timestamp' in elem:
                    msg.timestamp = float(re.search(r'[0-9]*\.+[0-9]{6}', elem).group(0))

                elif 'ID' in elem:
                    msg.arbitration_id = int(re.search(r'0*[0-9]+', elem).group(0))

                elif 'X' in elem or 'S' in elem or 'E' in elem or 'R' in elem or 'F' in elem:
                    msg.is_extended_id = True if 'X' in elem else False
                    msg.is_error_frame = True if 'E' in elem else False
                    msg.is_remote_frame = True if 'R' in elem else False
                    msg.is_fd = True if 'F' in elem else False

                elif 'DLC' in elem:
                    msg.dlc = int(re.search(r'[0-9]+', elem).group(0))
                    msg.data = bytearray(msg.dlc)

                elif "Channel" in elem:
                    pass

                elif re.findall(r'[0-9a-f]{2}', elem):
                    cont = 0
                    # print(elem)
                    for byte in re.findall(r'[0-9a-f]{2}', elem):
                        # print("byte:{}".format(byte))
                        msg.data[cont] = int(byte, 16)
                        cont += 1

            timestamp = msg.timestamp
            if first_timestamp == 0:
                first_timestamp = msg.timestamp
            print(str(msg_cont) + str(msg), file=log_file)
            msg_cont += 1
            # print(msg.arbitration_id)

            # ----------------------------------------------------
            # Decodifica degli oggetti can.Message
            # ----------------------------------------------------
            if msg.arbitration_id < 6 and msg.arbitration_id > 0:
                rec_msg = messageCodec(db, msg=msg).get_data()

                """Ricezione del messaggio"""
                if rec_msg[0] == db.get_message_by_name("Steer").frame_id:
                    degree_read = (rec_msg[1]["Degree"] - num_section_steer)
                    steer = degree_read / num_section_steer

                elif rec_msg[0] == db.get_message_by_name("Pedal").frame_id:
                    throttle_read = (rec_msg[1]["Throttle"])
                    brake_read = (rec_msg[1]["Brake"])
                    throttle = (throttle_read / num_section_pedals) / 2
                    brake = (brake_read / num_section_pedals) / 2

                elif rec_msg[0] == db.get_message_by_name("GearMsg").frame_id:
                    gear = rec_msg[1]["Gear"]
                    reverse = rec_msg[1]["Reverse"]
                    reverse = bool(reverse)
                    gear = gear - 1

                elif rec_msg[0] == db.get_message_by_name("Status").frame_id:
                    speed = rec_msg[1]["Speed"] / max_speed_spedometer
                    T_engine = ((rec_msg[1]["T_engine"] * interval_T_engine) + min_T_engine) / max_T_engine
                    rpm = ((rec_msg[1]["rpm_engine"] * interval_rpm) + min_rpm) / max_rpm

                    acceleration = (speed - speed_old) / (timestamp - timestamp_old)

                    speed_old = speed
                    timestamp_old = timestamp

                elif rec_msg[0] == db.get_message_by_name("Control_msg").frame_id:
                    th_state = True if rec_msg[1]["Th_state"] == 1 else False

                    if steer < -0.6:
                        swerve = -1
                    elif -0.6 <= steer < -0.2:
                        swerve = -0.5
                    elif -0.2 <= steer < 0.2:
                        swerve = 0
                    elif 0.2 <= steer < 0.6:
                        swerve = 0.5
                    elif steer >= 0.6:
                        swerve = 1

                    # ----------------------------------------------------
                    # Aggiornamento del buffer
                    # ----------------------------------------------------
                    status_buf.add_status(
                        {'gear': gear, 'cooling': th_state, 'rpm': rpm, 'throttle': throttle, 'steer': steer,
                         'brake': brake, 'Engine_temp': T_engine, 'speed': speed,
                         'swerve': swerve, 'acceleration': acceleration}, timestamp)
                    # flag_16 serve a stabilire ogni quanti n-ple (di default 7) deveessere richiamata la rete
                    # bayesiana per effettuare una classificazione
                    if flag_16 == 7:
                        flag_calc_belief = True
                        flag_16 = 0
                    else:
                        flag_16 += 1

                # print("{}---".format(flag_16), end='')
                # print(msg)
                # ----------------------------------------------------
                # Applicazione della rete bayesiana
                # ----------------------------------------------------
                if flag_calc_belief:
                    print("Calcolo")
                    last_status = status_buf.get_last_status()
                    dict_evidence = last_status.get_dict_by_keys(list_evidence_node)
                    print(dict_evidence)
                    start = timer()
                    pred, max_pred_class, val_pred_class = ids.predict(dict_evidence)
                    end = timer()
                    print("classificazione numero: {}".format(cont_bayes), file=log_file)
                    print("exec time: {}".format(end - start), file=log_file)
                    exec_time_list.append(end - start)
                    print("status rete--------------------------", file=log_file)
                    print(last_status, file=log_file)
                    print("predizione---------------------------", file=log_file)
                    print(pred[attack_index], file=log_file)
                    # viene riconosciuto l'attacco se la probabilità calcolata dalla rete sia <= 0.6
                    if val_pred_class[attack_index]['(0.5-inf)'] >= 0.6:
                        print("--------------attacco riconosciuto-------------")
                        print("--------------attacco riconosciuto-------------", file=log_file)
                        rel_atk_list.append(1)
                    else:
                        rel_atk_list.append(0)

                    flag_calc_belief = False
                    cont_bayes += 1

        atk_time = (csv_last_time - csv_first_time)/1000
        print("Tipologia di attacco: {}".format(atk_type), file=summary_file)
        # print("Istante dell'attacco (s):{}".format(atk_time), file=summary_file)

        print("Lista dei tempi di esecuzione", file=summary_file)
        print(exec_time_list, file=summary_file)
        print("Tempo di esecuzione medio(s): {}".format(np.mean(exec_time_list)), file=summary_file)
        print("Tempo di esecuzione massimo(s): {}".format(np.max(exec_time_list)), file=summary_file)
        print("Tempo di esecuzione minimo(s): {}".format(np.min(exec_time_list)), file=summary_file)

        print("Numero classificazioni: {}".format(cont_bayes), file=summary_file)
        print("Lista rilevamenti", file=summary_file)
        print(list(range(0,cont_bayes)), file=summary_file)
        print(rel_atk_list, file=summary_file)
        print("", file=summary_file)


finally:
    log_file.close()
    summary_file.close()
    reader.close()

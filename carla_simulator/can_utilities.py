#!/usr/bin/env python
# coding: utf-8
"""
In questo file sono implementate funzioni e classi uili per la decodifica e la codifica dei messaggi CAN
"""

import sys
import os
import cantools
import can
from can.listener import Listener
import serial
import socket

# TODO implementare invio/ricezione tramite UDP con struct

def msg_to_string(msg, sep="*"):
    """
    Questa funzione serve a convertire un messaggio CAN (oggetto 'can.Message' definito nel modulo 'python-can')
    in una stringa cosi da poter essere trasferito tramite UDP. La stringa è formata dai vari campi del messagio
    CAN separati dal carattere 'sep'.

    :param can.Message msg: messaggio CAN da trasformare in stringa
    :param stringa sep: carattere separatore

    :return: Messaggio CAN convertito in stringa
    :rtype: stringa
    """

    list_bytes = []

    field_strings = [str(msg.timestamp)]
    field_strings.append(str(msg.arbitration_id))
    field_strings.append(str(msg.is_extended_id))
    field_strings.append(str(msg.is_remote_frame))
    field_strings.append(str(msg.is_error_frame))
    field_strings.append(str(msg.channel))
    field_strings.append(str(msg.dlc))

    for elem in msg.data:
        list_bytes.append(elem)
    field_strings.append(str(list_bytes))

    field_strings.append(str(msg.is_fd))
    field_strings.append(str(msg.bitrate_switch))
    field_strings.append(str(msg.error_state_indicator))

    return sep.join(field_strings)

def decode_udp_msg(message_udp, sep="*"):
    """
    Questa funzione serve a convertire in un messaggio CAN una stringa ricevuta tramite tramite protocollo UDP creata
    tramite la funzione ``msg_to_string()``.

    :param stringa message_udp: Stringa ricevuta tramite UDP
    :param stringa sep: Carattere separatore

    :return: Messaggio CAN
    :rtype: can.Message
    """
    #message_udp = message_udp.split(sep)

    msg = can.Message()
    for i in range(0, len(message_udp)):
        if message_udp[i]=='False':
            message_udp[i]=False

    msg.timestamp = float(message_udp[0])
    msg.arbitration_id = int(message_udp[1])
    msg.is_extended_id = bool(message_udp[2])
    msg.is_remote_frame = bool(message_udp[3])
    msg.is_error_frame = bool(message_udp[4])

    if (message_udp[5]) is str:
        msg.channel = str(message_udp[5])
    elif (message_udp[5]) is int:
        msg.channel = int(message_udp[5])
    else:
        msg.channel = None

    msg.dlc = int(message_udp[6])

    msg_data = message_udp[7]
    msg_data = msg_data[1:-1]
    msg_data = msg_data.split(',')

    msg.data = bytearray(msg.dlc)
    cont = 0
    for elem in msg_data:
        msg.data[cont] = int(elem, 10)
        cont += 1

    msg.is_fd = bool(message_udp[8])
    msg.bitrate_switch = bool(message_udp[9])
    msg.error_state_indicator = bool(message_udp[10])

    return msg

class messageCodec:
    """
    | In questa classe sono implementati i metodi per la creazione del messaggio CAN e
        la codifica e la decodifica del payload in base alle informazioni sulla struttura del messaggio
        fornite dal database. Il messaggio CAN creato è un oggetto 'can.Message' la cui classe è definita nel modulo 'python-can'.
    | In ingresso devono essere forniti o il messaggio CAN (per manipolare un messaggio già esistente)
        o il nome del messaggio (per creare da zero un messaggio la cui struttura è descritta nel database).

    :param db: Contiene tutte le informazioni presenti nel database di messaggi CAN
    :type db: cantools.database.can.database.Database
    :param msg: Messaggio CAN
    :type msg: can.Message
    :param msg_name: Nome del messaggio CAN
    :type msg_name: stringa

    **Metodi:**
    """
    def __init__(self, db, msg=None, msg_name=None):
        """
        :param db: Contiene tutte le informazioni presenti nel database di messaggi CAN
        :type db: cantools.database.can.database.Database
        :param msg: cantools.database.can.database.Database
        :param msg: Messaggio CAN
        :param msg_name: Nome del messaggio CAN
        :type msg_name: stringa
        """
        self.msg_structure = None
        self.signals_dict = {}
        self.db = db
        if(msg_name != None):
            self.set_msg_name(self.db, msg_name)
            
        elif(msg != None):
            self.set_msg(self.db, msg)

    def set_msg_name(self, db, msg_name):
        """
        | Metodo per recuperare la struttura del messaggio CAN dal database, dato il nome del messaggio.
        | Tale struttura viene memorizzata all'interno dell'attributo 'self.msg_structure',
            un oggetto di tipo 'cantools.database.can.message.Message' la cui classe è definita nel modulo 'cantools'.

        :param db: Contiene tutte le informazioni presenti nel database di messaggi CAN
        :type db: cantools.database.can.database.Database
        :param msg_name: Specifica il nome del messaggio che deve essere cercato nel database
        :type msg_name: stringa
        """
        self.msg_structure = db.get_message_by_name(msg_name)
        self.dlc = self.msg_structure.length
        self.signals = self.msg_structure.signals

    def set_msg(self, db, msg):
        """
        Metodo per recuperare la struttura del messaggio CAN dal database, dato un oggetto 'can.Message'.
        Tale struttura viene memorizzata all'interno dell'attributo 'self.msg_structure', un oggetto di tipo
        'cantools.database.can.message.Message' la cui classe è definita nel modulo 'cantools'.

        :param db: Contiene tutte le informazioni presenti nel database di messaggi CAN
        :type db: cantools.database.can.database.Database
        :param msg: Contiene tutte le informazioni che descrivono il messaggio CAN
        :type msg: can.Message
        """
        self.msg = msg
        self.msg_structure = db.get_message_by_frame_id(self.msg.arbitration_id)
        self.dlc = self.msg_structure.length
        self.signals = self.msg_structure.signals
  
        self.data_payload = self.msg.data        
        self.extract_data()

    def create_data(self, data):
        """
        Questo metodo serve per la creazione del payload del messaggio CAN. Il metodo prende in ingresso i
        dati sottoforma di un dizionario.

        :param data: Contiene le coppie {nome_segnale (stringa): valore (float)} che serviranno a
            creare il payload
        :type data: dizionario

        :return: Contiene i byte che andranno a formare il payload del messaggio CAN. La lunghezza dipende
            dal valore Data Length Code (DLC) specificato nella struttura del messaggio
        :rtype: bytearray
        """
        temp = 0
        cont = 0
        len_data_error = []
        
        and_mask = 255
        data_payload = bytearray(self.dlc)
        
        if(self.msg_structure == None):
            print("messaggio non trovato o non fornito")
            return None
            
        else:
            for signal in self.signals:
                if(signal.byte_order == 'little_endian'):
                    #controllo sui byte in cui scrivere i dati a partire dal bit di start
                    #e dalla lunghezza del segnale
                    begin_byte = (signal.start)//8
                    end_byte = (signal.start + signal.length)//8
                    bytes_to_change = data_payload[begin_byte:end_byte+1]
                    cont_bit = signal.length
                    cont_byte = 0
                    
                    for elem in bytes_to_change:
                        #se il segnale interessa più byte, per ogni byte si prende il dato e da questo si prende
                        #la parte che bisogna scrivere nel byte
                        if(len(bytes_to_change) > 1):
                            if(cont_bit == signal.length):
                                #byte che contiene la parte iniziale del segnale
                                temp_data = data[signal.name] & (and_mask >> (signal.start%8))
                                temp_data = temp_data << signal.start%8
                                temp = int(elem) | temp_data
                                cont_bit -= (8 - signal.start%8)
                                data_payload[begin_byte] = temp
                            elif((cont_bit > 8) and (cont_bit < signal.length)):
                                temp_data = data[signal.name] >> (cont_bit - 8)
                                temp_data = temp_data & and_mask
                                temp = int(elem) | temp_data
                                data_payload[begin_byte+cont_byte] = min(temp, 255)
                                data_payload[begin_byte + cont_byte] = max(data_payload[begin_byte+cont_byte], 0)
                                cont_bit -= 8
                            else:
                                #byte che contiene la parte finale del segnale
                                temp_data = data[signal.name]
                                temp_data = temp_data & (and_mask >> (8 - cont_bit))
                                temp = int(elem) | temp_data
                                data_payload[end_byte] = min(temp, 255)
                                data_payload[end_byte] = max(data_payload[end_byte], 0)
                
                            cont_byte += 1
                        #se il segnale interessa un solo byte, si prende il dato e si scrive nella posizione opportuna
                        else:
                            temp_data = data[signal.name]
                            temp = int(elem) | (temp_data << (signal.start%8))
                            # print("temp: {}".format(temp))
                            data_payload[begin_byte] = min(temp, 255)
                            data_payload[begin_byte] = max(data_payload[begin_byte], 0)
                
                
                elif(signal.byte_order == 'big_endian'):
                    begin_byte = ((signal.start)//8)
                    end_byte = ((7 - signal.start%8) + signal.length + signal.start - (1 + signal.start%8))//8#da migliorare
                    bytes_to_change = data_payload[begin_byte:end_byte+1]
                    cont_bit = signal.length
                    cont_byte = 0
                    
                    for elem in bytes_to_change:
                        
                        if(len(bytes_to_change) > 1):
                            if(cont_bit == signal.length):
                                #byte che contiene la parte finale del segnale
                                temp_data = data[signal.name] >> (cont_bit - (signal.start%8 + 1))
                                temp = int(elem) | temp_data
                                cont_bit -= (signal.start%8 + 1)
                                data_payload[begin_byte] = min(temp, 255)
                                data_payload[begin_byte] = max(data_payload[begin_byte], 0)
                            elif((cont_bit > 8) and (cont_bit < signal.length)):
                                temp_data = data[signal.name] >> (cont_bit - 8)
                                temp_data = temp_data & and_mask
                                temp = int(elem) | temp_data
                                data_payload[begin_byte+cont_byte] = min(temp, 255)
                                data_payload[begin_byte+cont_byte] = max(data_payload[begin_byte+cont_byte], 0)
                                cont_bit -= 8
                            else:
                                #byte che contiene la parte iniziale del segnale
                                #viene presa la parte di interesse del dato e shiftata di una quantità opportuna
                                #cosi da essere posizionata all'interno del byte
                                temp_data = data[signal.name]
                                temp_data = temp_data & (and_mask >> (8 - cont_bit))
                                temp_data = temp_data << (8 - cont_bit)
                                temp = int(elem) | temp_data
                                data_payload[end_byte] = min(temp, 255)
                                data_payload[end_byte] = max(data_payload[end_byte], 0)
                            cont_byte += 1
                        else:
                            temp_data = data[signal.name]
                            temp = int(elem) | (temp_data << (signal.start%8))
                            data_payload[begin_byte] = min(temp, 255)
                            data_payload[begin_byte] = max(data_payload[begin_byte], 0)
        
        return data_payload

    def extract_data(self):
        """
        Questo metodo serve per l'estrazione del payload del messaggio CAN. Il metodo prende il payload
        (contenuto nell'attributo 'data_payload') sottoforma di oggetto bytearray e memorizza i dati all'interno
        dell'attributo 'signals_dict' sottoforma di dizionario {nome_segnale (stringa): valore (float)}.
        """
        and_mask = 255
        
        if(self.msg_structure == None):
            print("messaggio non trovato o non fornito")
            return None
        
        for signal in self.signals:
            signal_data = 0
            if(signal.byte_order == 'little_endian'):
                begin_byte = (signal.start)//8
                end_byte = (signal.start + signal.length - 1)//8
                bytes_to_read = self.data_payload[begin_byte:end_byte+1]
                
                cont_bit = signal.length
                cont_byte = 0
                
                for elem in bytes_to_read:
                    if(len(bytes_to_read) > 1):
                        pass
                
                    else:
                        temp = (int(elem) >> (signal.start%8))
                        temp = temp & (and_mask >> (8 - signal.length))
                        signal_data = temp
                       
            elif(signal.byte_order == 'big_endian'):
                begin_byte = (signal.start)//8
                end_byte = ((7 - signal.start%8) + signal.length + signal.start - (1 + signal.start%8))//8#da migliorare
                bytes_to_read = self.data_payload[begin_byte:end_byte+1]
                cont_bit = signal.length
                cont_byte = 0
                
                for elem in bytes_to_read:
                    
                    if(len(bytes_to_read) > 1):
                        if(cont_bit == signal.length):
                            #in questo byte è contenuta l'ultima parte del dato
                            #dal bit 0 per una lunghezza che dipende dal valore del bit di start
                            temp = int(elem) & (and_mask >> (7 - signal.start%8))
                            signal_data = signal_data | temp
                            signal_data = signal_data << (cont_bit - (signal.start%8 + 1))
                            cont_bit -= (signal.start%8 + 1)
                        elif((cont_bit > 8) and (cont_bit < signal.length)):
                            #in questo caso il byte fa tutto parte del dato quindi lo prendo così come'è
                            temp = int(elem)
                            signal_data = signal_data | temp
                            signal_data = signal_data << (8*(len(bytes_to_read) - cont_byte - 1))
                            cont_bit -= 8
                        else:
                            #in questo byte è contenuta ll prima parte del dato
                            #dal bit 7 per una lunghezza che dipende dal numero di bit rimasti nel segnale                           
                            temp = int(elem) >> (8 - cont_bit)
                            temp = temp & (and_mask >> (8 - cont_bit))
                            signal_data = signal_data | temp
                            
                        cont_byte += 1
                        
                    else:
                        temp = (int(elem) >> (7 - (signal.start%8)))
                        temp = temp & (and_mask >> (8 - signal.length))
                        signal_data = temp
            
            self.signals_dict[signal.name] = signal_data
        return None

    def get_data(self):
        """
        Il metodo restituisce una lista che contiene l'id del messaggio e il dizionario
        {nome_segnale (stringa): valore (float)}.

        :return: Id del messaggio e il dizionario {nome_segnale (stringa): valore (float)}
        :rtype: lista
        """
        return [self.msg_structure.frame_id, self.signals_dict]

    def create_msg(self, data):
        """
        In questo metodo, a partire dai dati del payload e dalla struttura del messaggio CAN specificata nel database,
        viene istanziato e restituito un oggetto 'can.Message'.

        :param data: Il payload da inserire nel messaggio CAN
        :type data: bytearray

        :return: Messaggio CAN
        :rtype: can.Message
        """
        self.msg = can.Message(timestamp=0.0, is_remote_frame=False, is_extended_id=self.msg_structure.is_extended_frame,\
                            is_error_frame=False, arbitration_id=self.msg_structure.frame_id, dlc=self.dlc, data=data,\
                            is_fd=False, bitrate_switch=False, error_state_indicator=False, channel=None)
        
        return self.msg

class Sender(Listener):
    """
    Classe per la gestione dell'inoltro tramite UDP dei messaggi CAN. In questa classe sono implementati i metodi
    per la ricezione del messaggio CAN sul bus e per l'elaborazione e l'inoltro del messaggio stesso tramite UDP.

    :param udp_ip: Indirizzo ip di destinazione
    :type udp_ip: stringa
    :param udp_port: Porta di destinazione
    :type udp_port: int
    """
    def __init__(self, udp_ip, udp_port):
        """
        Costruttore di Sender. Al metodo ``__init__()`` devono essere forniti l'indirizzo ip e la porta del dispositivo\
        a cui si vogliono inoltrare i messaggi CAN ricevuti sul bus. Al suo interno viene inizializzato il socket.

        :param stringa udp_ip: indirizzo ip di destinazione
        :param intero udp_port: porta di destinazione
        """
        super().__init__()
        self.server_address = (udp_ip, udp_port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def on_message_received(self, msg):
        """
        Questo metodo è eseguito non appena viene ricevuto un messaggio sul bus, è un override di un metodo della \
        classe padre Listener. La class Listener è definita nel modulo 'python-can'.

        :param msg: Messaggio CAN
        :type msg: can.Message
        """
        message = msg_to_string(msg)
        sent = self.sock.sendto(message.encode(), self.server_address)
        print("messaggio ricevuto")

    def stop(self):
        """
        Questo metodo viene eseguito per rilasciare le risorse occupate dall'oggetto, è un override di un metodo
        della classe padre Listener. La class Listener è definita nel modulo 'python-can'.
        """
        self.sock.close()



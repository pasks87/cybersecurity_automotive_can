import math
import numpy as np
from config import *

class LookUpTable():
    """
    Questa classe serve a gestire look up table in una o più dimensioni

    :param labels: Lista contenente le etichette di righe e colonne
    :type labels: lista
    :param lut_value: Liste annidate che servono a memorizzare i valori all'internto delle look up table
    :type lut_value: lista

    **Metodi:**
    """

    def __init__(self, labels, lut_values):
        """
        :param labels: Lista contenente le liste di etichette di righe e colonne
        :type labels: lista
        :param lut_value: Liste annidate che servono a memorizzare i valori all'internto delle look up table
        :type lut_value: lista
        """
        self.labels = labels
        self.values = lut_values

    def _search_lut_elem(self, input_list):
        """
        Ricerca e restituisce un elemento della look up table

        :param input_list: Lista degli input da fornire alla look up table
        :type input_list: lista
        :return: Valore recuperato dalla look up table
        :rtype: float
        """
        temp = self.values
        for input_elem in input_list:
            num_label_list = input_list.index(input_elem)
            temp = temp[self.labels[num_label_list].index(input_elem)]
            # print("Label: {}, Num elem label: {} Num label: {}".format(input_elem,
            #     self.labels[num_label_list].index(input_elem), num_label_list))
            # print("Selected elem: {}".format(temp))

        return temp

    def get_value(self, input_list):
        """
        A partire dagli input restituisce il valore corrispondente della look up table effettuando se necessario
            un opportuna interpolazione.

        :param input_list: Lista degli input da fornire alla look up table
        :type input_list: lista
        :return: Valore recuperato dalla look up table
        :rtype: float
        """
        # Approssimazione dei valori da fornire come label
        # per ora si becca il primo label che risulta maggiore rispetto al valore fornito
        # TODO effettuare interpolazione lineare tra i valori
        label_value_list = [0] * len(input_list)

        for input_elem in input_list:
            num_label_list = input_list.index(input_elem)
            label_list = self.labels[num_label_list]
            if input_elem <= label_list[0]:
                label_value_list[num_label_list] = label_list[0]
            elif input_elem >= label_list[-1]:
                label_value_list[num_label_list] = label_list[-1]
            else:
                for cont, elem in enumerate(label_list[0:-1]):
                    if input_elem > elem and input_elem <= label_list[cont+1]:
                        label_value_list[num_label_list] = label_list[cont+1]

        # print("Lista valori: {}".format(label_value_list))
        return self._search_lut_elem(label_value_list)


class EngineSubModel():
    """
    Questa classe implementa il sotto-modello "Engine" che descrive il comportamente del motore.
    Rispetto al modello descritto nel paper:
    * Nessun ricircolo del gas di scarico

    **Metodi:**
    """
    def __init__(self):
        self.N_engine = 0
        self.N_engine_old = self.N_engine
        self.N_pump = 0
        self.P_t = 0
        self.m_egr = 0
        self.T_egr = 0

        # Parametri specifici del motore
        self.engine_gear = [42.8, 23.0, 14.1, 10.1, 8.1]
        self.N_idle = 750.0
        self.i_p = 1.158
        N_engine_labels = [1500.0, 2000.0, 25000.0, 3000.0, 3500.0, 4000.0]
        ch_labels = [0, 12.5, 25.0, 37.5, 50.0, 62.5, 75.0, 87.5, 100.0]
        labels = [ch_labels, N_engine_labels]
        values = [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                  [3.4, 4.6, 5.9, 6.8, 8.2, 9.5],
                  [7.2, 9.8, 11.5, 13.9, 16.7, 18.5],
                  [10.5, 14.1, 17.7, 20.8, 24.8, 28.2],
                  [14.0, 18.9, 23.6, 28.0, 33.1, 37.1],
                  [17.5, 23.9, 29.2, 35.2, 41.3, 50.9],
                  [21.5, 28.1, 35.1, 41.7, 49.5, 51.2],
                  [22.0, 33.4, 41.9, 46.7, 51.5, 51.2],
                  [22.0, 34.0, 43.2, 49.0, 51.5, 51.2]]
        self.P_t_lut = LookUpTable(labels, values)

    def update(self, v, i, ch):
        """
        Prende in ingresso velocità, marcia e la posizione dell'acceleratore (carico) per calcolare alcuni parametri
            danno informazioni sul funzionamento del motore.
        In particolare questi parametri sono (tra parentesi si può osservare l'unità di misura):
        * N_engine (rpm): Numero di giri del motore della vettura;
        * N_pump (rpm): Numero di giri del motore della pompa che fa circolare il liquido di raffereddamento
            all'interno del sistema di raffreddamento;
        * P_t (kW): Potenza termica trasferita dal motore al liquido di raffreddamento.

        :param v: Velocità del veicolo (km/h)
        :type v: float
        :param i: Marcia del veicolo (adimensionale,da 1-5)
        :type i: int
        :param ch: posizione dell'acceleratore del pedale dell'acceleratore (percentuale)
        :type ch: float
        """
        # v serve in m/s
        if i >= 0:
            gear = i
        else:
            gear = 1

        if gear == 0:
            self.N_engine = self.N_engine_old
        else:
            N_engine = ((v*30)/(math.pi*3.6))*self.engine_gear[gear-1]
            self.N_engine = N_engine if N_engine > self.N_idle else self.N_idle
            self.N_engine_old = self.N_engine

        self.N_pump = self.N_engine * self.i_p

        self.P_t = self.P_t_lut.get_value([ch, self.N_engine])


class AerodynamicsSubModel():
    """
    Questa classe implementa il sotto-modello "Aerodynamics" che decrive il comportamento del radiatore
    Rispetto al modello descritto nel paper:
    * La ventola può trovarsi solo nelle modalità accesa (duty-cycle 80%) o spenta (duty-cycle 0%)
    * Viene trascurato l'effetto del condizionatore in cabina

    **Metodi:**
    """
    def __init__(self):
        self.m_rad = 0.0

        #Fan On - veicolo fermo
        # Visto che il duty cycle dell ventola è fissato queste quantità sono tutte costanti
        self.A_rad = -300000.0
        self.B_rad = -5070000.0
        #self.B_rad = -3880000.0
        self.C_rad = 346
        #self.C_rad = 64
        self.K1_rad = 0.0001
        self.k2_rad = 0.0904

        a = self.A_rad - self.K1_rad
        b = self.B_rad - self.k2_rad
        c = self.C_rad
        temp = list(np.roots([a, b, c]))

        self.m_rad_fan = temp[0] if temp[0] > 0 else temp[1]

        #Fan off - veicolo  in movimento
        self.m_rad_v = 0.0
        self.c1_rad = 0.135
        self.c2_rad = 21.458

        #Condizioni generiche
        self.alfa = 1.0

    def update(self, v, fan):
        """
        Prende in ingresso la velocità e lo stato della ventola per calcolare alcuni parametri che
            danno informazioni sullo stato del flusso d'aria che interessa il radiatore
        In particolare questi parametri sono (tra parentesi si può osservare l'unità di misura):
        * m_rad (g/s): Portata del flusso d'aria che interessa il radiatore.

        :param v: Velocità del veicolo (km/h)
        :type v: float
        :param fan: Stato della ventola del radiatore (ON, OFF)
        :type fan: bool
        """
        if not fan:
            self.alfa = 1
            fan_flow = 0
        else:
            self.alfa = 0.8
            fan_flow = self.m_rad_fan

        self.m_rad_v = (self.c1_rad * v * v) + self.c2_rad * v
        self.m_rad = fan_flow + (self.alfa * self.m_rad_v)


class ThermostatSubModel():
    """
    Questa classe implementa il sotto-modello "controller/thermostat" che decrive il comportamento del sistema di
        controllo della ventola del radiatore e il modello del thermostato
    Rispetto al modello descritto nel paper:
    * Viene trascurato l'effetto del condizionatore in cabina

    :param T_threshold: Temperatura oltre il quale viene fatta partire la ventola del radiatore (K)
    :type T_threshold: float

    **Metodi:**
    """
    def __init__(self, T_threshold):
        """
        :param T_threshold: Temperatura oltre il quale viene fatta partire la ventola del radiatore (K)
        :type T_threshold: float
        """
        self.fi_bypass = 1
        self.fi_rad = 0

        self.fan_rad = False
        self.T_threshold = T_threshold

        self.K_rad = 5.0
        self.exp_k_rad = math.exp(-self.K_rad)
        self.K_bypass = 1.0
        self.exp_k_bypass = math.exp(-self.K_bypass)

        self.T_percent = 0

        self.Th_start = 82.31
        self.Th_end = 98.78

        self.x_percent = 0

        self.A_th = 4.642
        self.B_th = -10.401
        self.C_th = 5.7668
        self.D_th = 0.1115
        self.E_th = 0.8724

    def set_threshold(self, T_threshold):
        """
        Metodo che serve a modificare la temperatura di soglia oltre la quale parte la ventola
            del radiatore
        :param T_threshold: Temperatura oltre il quale viene fatta partire la ventola del radiatore (K)
        :type T_threshold: float
        """
        self.T_threshold  = T_threshold

    def update(self, Th):
        """
        Prende in ingresso la temperatura del motore (per essere più precisi la temperatura del liquido di
            raffreddamenteo a contatto con il motore) per calcolare alcuni parametri danno informazioni
            sul sistema di controllo e sul termostato
        In particolare questi parametri sono (tra parentesi si può osservare l'unità di misura):
        * fan_rad (ON/OFF): Stato della ventola
        * fi_rad (adimensionale 0-1): Grado di apertura dell'uscita del termostato che porta al radiatore
        * fi_bypass (adimensionale 0-1): Grado di apertura dell'uscita del termostato che porta al circuito di bypass

        :param Th: Temperatura del motore (K)
        :type Th: float
        """
        self.T_percent = (Th - self.Th_start)/(self.Th_end - self.Th_start)
        self.x_percent = self.A_th * pow(self.T_percent,5) + self.B_th * pow(self.T_percent,4) + \
                         self.C_th * pow(self.T_percent,3) + self.D_th * pow(self.T_percent,2) + \
                         self.E_th * pow(self.T_percent,1)
        self.fi_rad = (1 - math.exp(-self.K_rad*self.x_percent))/(1 - self.exp_k_rad)
        self.fi_bypass = (1 - math.exp(self.K_bypass * self.x_percent - 1)) / (1 - self.exp_k_bypass)

        self.fan_rad = True if Th >= self.T_threshold else False


class HydraulicsSubModel():
    """
    Questa classe implementa il sotto-modello "hydraulics" che decrive il comportamento del sistema idraulico
        del veicolo
    """
    def __init__(self):
        pass

    def update(self):
        pass


class TempSubModel():
    """
    Questa classe serve ad implementare il sotto-modello che descrive la variazione di temperatura nel motore
        quando è in funzione e non l'impianto di raffreddamento
    """
    def __init__(self):
        self.T_norm = 363

        self.eps_T = 10

        self.T_engine = self.T_norm
        self.alfa = 1.0
        self.alfa_old = self.alfa
        self.t_start = 0 #istante di tempo in cui inizia il malfunzionamento
        self.q_temp_engine = self.T_norm

        # Parametri per il calcolo di alfa rispetto alla velocità
        # Temperatura ottimale 90 gradi celsius (363 K), temperatura massima 140 gradi celsius (413)
        #   a 0 Km/h si passa da 90 a 140 in 12 sec
        #   a 100 km/h (27.778 m/s) si passa da 90 a 140 in 4 sec
        #   alfa_0 e alfa_100 sonostati calcoati con qst dati
        T_max = 413.0
        t_v0 = 12.0
        t_v100 = 4.0

        alfa_0 = (T_max -  self.T_norm)/t_v0
        # print(alfa_0)
        v_0 = 0
        alfa_100 = (T_max -  self.T_norm)/t_v100
        # print(alfa_100)
        v_100 = 27.778

        self.m_temp = (v_100 - v_0)/(alfa_100 - alfa_0)
        self.q_temp = v_0 - (self.m_temp * alfa_0)

    def _calc_alfa(self, v):
        """
        Nota la velocità serve a calcolare il coefficiente angolare della retta che descrive la variazione di
            temperatura nel motore quando non è in funzione il sistema di raffredamento
        :param v: Velocità del veicolo
        :type v: float
        :return: Coefficiente angolare della retta
        :rtype: float
        """
        return ((v / 3.6) - self.q_temp)/self.m_temp

    def update(self, v, th_state, timestamp):
        """
        Prende in ingresso la velocità del veicolo, e lo stato del sistema di raffreddamento (ON/OFF) per calcolare
            la temperatura del motore T_engine (K).

        :param v: Velocità del veicolo
        :type v: float
        :param th_state: Stato del sistema di raffreddamento (ON=True, OFF=False)
        :type th_state: bool
        :param timestamp: Intervallo di tempo trascorso dall'inizio della simulazione (in millisecondi)
        :type timestamp: float
        """
        if th_state:
            self.T_engine = self.T_norm
            self.q_temp_engine = self.T_norm
            self.t_start = 0
        else:
            self.alfa = self._calc_alfa(v)
            # print("alfa:{}".format(self.alfa))
            # print("alfa_old:{}".format(self.alfa_old))

            if self.t_start == 0:
                self.t_start = timestamp
                t = (timestamp - self.t_start) / 1000
                self.T_engine = self.alfa_old * t + self.q_temp_engine

            else:
                t = (timestamp - self.t_start) / 1000 # mi serve il tempo in secondi
                # print("t:{}".format(t))
                temp = self.alfa_old * t + self.q_temp_engine
                self.T_engine = temp if temp < (max_temp_engine-10) else (max_temp_engine-10)
                # print("T_engine (physic): {}".format(self.T_engine))
                if self.alfa != self.alfa_old:
                    self.q_temp_engine = self.T_engine - (t * self.alfa)
                    self.alfa_old = self.alfa

                # self.T_engine = self.alfa * t + self.q_temp_engine
from xml.dom import minidom
import matplotlib.pyplot as plt
import numpy as np
import pomegranate
import re

class BayesGraph:
    """
    | Classe che contiene tutte le informazioni necessarie all'implementazione della rete bayesiana.
    | La rete viene costruita grazie a Weka e viene esportata in un file in formato XML. In particolare il file XML
        conterrà:

    * L'elenco dei nodi
    * I genitori di ogni nodo
    * La distribuzione di probabilità o la cpt associate ad ogni nodo
    * L'elenco delle classi in cui possono essere reggruppati i valori che può assumere ogni nodo

    | Nel metodo ``__init_()`` della classe viene caricato il file XML, ne viene effettuato il parsing e le informazioni
        di interesse (elenco dei nodi, genitori di ogni nodo, ecc.) vengono salvate negli attributi della classe.
    | Tramite il metodo ``create_graph()``, a partire delle informazioni precedentemente calcolate, sarà possibile costruire
        la rete bayesiana vera e propria.

    :param name_file: Percorso del file XML da caricare
    :type name_file: stringa

    **Metodi:**

    """
    def __init__(self, name_file):
        """
        Inizializzazione

        :param name_file: percorso del file XML da cariacare
        :type name_file: stringa
        """
        self.nodes_list = []  # lista con i nomi dei nodi
        self.nodes = {}  # contiene le coppie {"nome nodo": nodo} in cui nodo contiene la CPT o una distribuzione di probabilità
        self.name_classes_nodes = {}  # contiene la coppia {"nome nodo": lista con nomi delle classi}
        self.cpt_nodes = {}  # cpt dei nodi
        self.parents = {}  # dizionario i cui valori sono liste con nodi genitori di ciascun nodo
        self.tree = minidom.parse(name_file)  # contiene tutti i dati del file XML organizzati ad albero
        self._load()

    def _load(self):
        """
        Metodo per effettuare il parsing del file XML che contiene la descrizione della rete bayesiana
        """
        for elem in self.tree.getElementsByTagName("VARIABLE"):
            name = elem.getElementsByTagName("NAME")[0].firstChild.data
            self.nodes_list.append(name)
            list_attributes = []
            for outcome in elem.getElementsByTagName("OUTCOME"):
                text = outcome.firstChild.data
                if text[0] == "'":
                    list_attributes.append(outcome.firstChild.data[3:-3])
                else:
                    list_attributes.append(outcome.firstChild.data)
            self.name_classes_nodes[name] = list_attributes

        for elem in self.tree.getElementsByTagName("DEFINITION"):
            name = elem.getElementsByTagName("FOR")[0].firstChild.data
            self.parents[name] = []
            given_elem = elem.getElementsByTagName("GIVEN")
            for parent in given_elem:
                self.parents[name].append(parent.firstChild.data)

            cpt = elem.getElementsByTagName("TABLE")[0].firstChild.data
            self.cpt_nodes[name] = self._cpt_str_to_list(cpt)

        # riordino la lista dei nodi in modo ceh nella funzione create_graph() non vengano create CPT che dipendono
        # da altre CPT non ancora definite
        temp_nodes_list = self.nodes_list.copy()
        self.nodes_list = []

        while len(temp_nodes_list) != len(self.nodes_list):
            # print("temp_nodes_list: {}".format(temp_nodes_list))
            # print("node list: {}".format(self.nodes_list))
            for i in range(len(temp_nodes_list)):
                # print("i: {}".format(i))
                if not self.parents[temp_nodes_list[i]]:
                    # print("parents: {}".format(self.parents[temp_nodes_list[i]]))
                    if not temp_nodes_list[i] in self.nodes_list:
                        self.nodes_list.append(temp_nodes_list[i])
                else:
                    # print("parents: {}".format(self.parents[temp_nodes_list[i]]))
                    flag_append = True
                    for elem in self.parents[temp_nodes_list[i]]:
                        if elem not in self.nodes_list:
                            flag_append = False

                    if flag_append:
                        if not temp_nodes_list[i] in self.nodes_list:
                            self.nodes_list.append(temp_nodes_list[i])

    def _cpt_str_to_list(self, str_cpt):
        """
        Metodo per convertire la cpt in una lista di float a partire da una stringa

        :param str_cpt: stringa contenente la cpt
        :type str_cpt: stringa

        :return: Matrice contenente gli elementi della cpt
        :rtype: lista
        """
        cpt = []

        cpt_tmp = str_cpt.split(" \n")
        cpt_tmp.pop()
        cpt_tmp[0] = cpt_tmp[0][1:]
        for elem in cpt_tmp:
            cpt.append([float(i) for i in elem.split(" ")])

        return cpt

    def create_graph(self, name_network="Byesian netowrk"):
        """
        Metodo per create il modello di rete bayesiana (tramite pomegranate) a partire dai dati caricati dal file XML.

        :param name_network: nome della rete bayesiana
        :type name_network: stringa

        :return: Modello pomegranate della rete bayesiana
        :rtype: pomegranate.BayesianNetwork
        """

        cpt_node = {}
        pg_node = {}
        model = pomegranate.BayesianNetwork(name_network)

        for node_name in self.nodes_list:
            if not self.parents[node_name]:
                dict_dist = {}
                for elem in self.name_classes_nodes[node_name]:
                    dict_dist[elem] = self.cpt_nodes[node_name][0][self.name_classes_nodes[node_name].index(elem)]
                # print("name_prior: {}".format(node_name))
                self.nodes[node_name] = pomegranate.DiscreteDistribution(dict_dist)
                # print(self.nodes[node_name])
                pg_node[node_name] = pomegranate.Node(self.nodes[node_name], name=node_name)
            else:
                cpt_pg = []
                parent_list = self.parents[node_name].copy()
                parent_list.reverse()

                mod_list = [len(self.name_classes_nodes[node_name])]

                for i in range(len(parent_list) - 1):
                    mul = mod_list[i] * len(self.name_classes_nodes[parent_list[i]])
                    mod_list.append(mul)

                cont = 0
                for elem in self.cpt_nodes[node_name]:
                    for prob in elem:
                        row = [prob, self.name_classes_nodes[node_name][cont % mod_list[0]]]

                        for parent in parent_list:
                            attr = (cont // mod_list[parent_list.index(parent)]) % len(self.name_classes_nodes[parent])
                            row.append(self.name_classes_nodes[parent][attr])
                        cont += 1
                        row.reverse()
                        cpt_pg.append(row)
                cpt_node[node_name] = cpt_pg

        for node_name in self.nodes_list:
            if self.parents[node_name]:
                # print("parents: {}".format(self.parents[node_name]))
                parent_node_list = []
                for parent in self.parents[node_name]:
                    parent_node_list.append(self.nodes[parent])
                self.nodes[node_name] = pomegranate.ConditionalProbabilityTable(cpt_node[node_name], parent_node_list)
                # print("node {}: {}".format(node_name,self.nodes[node_name]))
                # print("parent_node_list: {}".format(parent_node_list))
                pg_node[node_name] = pomegranate.Node(self.nodes[node_name], name=node_name)

        for node_name in self.nodes_list:
            # le distribuzioni di output seguono l'ordine con cui vengono aggiunti i nodi qui
            model.add_node(pg_node[node_name])

        for node_name in self.nodes_list:
            # print("name {}".format(node_name))
            for parent in self.parents[node_name]:
                # print("parent {}".format(parent))
                model.add_edge(pg_node[parent], pg_node[node_name])

        model.bake()

        return model


class PlotBayesNode:

    def __init__(self, bg):
        self.bg = bg
        self.fig = plt.figure()
        self.ax = []
        self.y_classes = []
        self._init_ax()
        plt.ion()

    def _init_ax(self):
        for node in self.bg.nodes_list:
            self.ax.append(self.fig.add_subplot(len(self.bg.nodes_list), 1, (self.bg.nodes_list.index(node)) + 1))
            self.y_classes.append(np.arange(len(self.bg.name_classes_nodes[node])))

    def plot(self, dict_val, prediction, plt_pause=0.01):
        for node in self.bg.nodes_list:
            self.ax[self.bg.nodes_list.index(node)].clear()
            if node in dict_val.keys():
                print("node_evidence: {}".format(node))
            else:
                values = prediction[self.bg.nodes_list.index(node)].values()
                self.ax[self.bg.nodes_list.index(node)].barh(self.y_classes[self.bg.nodes_list.index(node)],
                                                             values, align='center')
                self.ax[self.bg.nodes_list.index(node)].set_title(node)
                plt.show()
        plt.pause(plt_pause)


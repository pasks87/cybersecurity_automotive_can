import re

class IdsClassBayes:
    """
    Classe in cui viene realizzato l'ids.

    :param network_graph: Rete bayesiana utilizzata dell'ids
    :type network_graph: ids.BayesGraph

    **Metodi:**

    """
    def __init__(self, network_graph):
        self.graph = network_graph  # oggetto di tipo bayesGraph
        self.model = self.graph.create_graph()  # modello della rete bayesiana

        # inizializzazione degli intervalli a partire dal nome delle classi
        self.interval = {}
        print("Calcolo classi nell'init di IdsClassBayes")
        for key, interval_list in self.graph.name_classes_nodes.items():
            print("key: {}".format(key))
            print("interval_list: {}".format(interval_list))
            if key == 'gear':
                self.interval[key] = [0, 1, 2, 3, 4]
            elif key == 'cooling':
                self.interval[key] = [True, False]
            elif key == 'at_light':
                self.interval[key] = [True, False]
            elif key == 'light':
                self.interval[key] = interval_list.copy()
            elif key == 'actor_collision':
                self.interval[key] = interval_list.copy()
            elif key == 'crossed_lane':
                self.interval[key] = interval_list.copy()
            else:
                self.interval[key] = self._interval_calc(interval_list)
            print("interval[key]: {}".format(self.interval[key]))

    def predict(self, dict_values):
        """
        Prende in ingresso i valori da mandare in ingresso alla rete (evindenza), restituisce la predizione effettuata
        dalla rete bayesiana e una lista contenente (per ciascun nodo) i nomi delle classi che,
        in seguito alla predeizione, risultano avere probabilità di accadimento maggiore

        :param dict_values: Dati da mandare in ingresso all'ids, questi sono specificati come un dizionario {nome_nodo: valore}
        :type dict_values: dizionario

        :return: Restituisce la predizione effettuata dalla rete bayesiana e una lista contenente le classi con \
        probabilità di accadimento maggiore
        :rtype: numpy.ndarray, lista
        """
        dict_class = {}
        for key, value in dict_values.items():
            # print("key: {}".format(key))
            # print("value: {}".format(value))
            dict_class[key] = self.selecter(key, value)
        # print(dict_class)
        prediction = self.model.predict_proba(dict_class)
        prediction_max_class = []
        prediction_prob_class = []
        for pred in prediction:
            # print(pred)
            if type(pred) is not str:
                max = 0
                max_key = ""
                dict_prob_class = {}
                for key, value in pred.items():
                    dict_prob_class[key] = value
                    if value > max:
                        max = value
                        max_key = key
                prediction_max_class.append(max_key)
                prediction_prob_class.append(dict_prob_class)
            else:
                prediction_max_class.append(pred)
                prediction_prob_class.append({pred: 100})
        return prediction, prediction_max_class, prediction_prob_class

    @staticmethod
    def _interval_calc(interval_list):
        """
        Weka suddivide i valori che può assumere un determinato nodo in varie classi che rappresentano intervalli
        numerici, questo metodo prende i nomi delle classi e restituisce una lista composta dagli estremi
        dei vari intervalli.
        | Es. ['(-inf--0.2]','(-0.2-0.5]','(0.5-inf)'] ---> [-0.2,0.5]

        :param interval_list: lista di stringhe che rappresentano vari intervalli numerici
        :type interval_list: lista

        :return: lista degli estremi dei vari intervalli
        :rtype: lista
        """
        values = []
        elements = []
        # print("interval list: {}".format(interval_list))
        for elem in interval_list:
            # print("elem: {}".format(elem))
            # 3 segni - : due numeri negativi
            if elem.count('-') == 3:
                elements = elements + re.findall("-0\.[0-9]{1,6}", elem)
            # 2 segni - e l'elemento non è il primo della lista: un elemento positivo e uno negativo
            elif elem.count('-') == 2 and interval_list.index(elem) != 0:
                # elements = elements + re.findall("-0\.[0-9]{1,6}", elem)
                tmp = re.findall("0\.[0-9]{1,6}", elem)
                tmp[0] = "-" + tmp[0]
                elements = elements + tmp
                zero = re.findall("-0]", elem)
                if zero:
                    elements = elements + [zero[0][1]]
            else:
                elements = elements + re.findall("0\.[0-9]{1,6}", elem)
                zero = re.findall("\(0-", elem)
                if zero:
                    elements = elements + [zero[0][1]]
            # print("elements: {}".format(elements))
        for x in elements:
            if float(x) not in values:
                values.append(float(x))
        values.sort()

        return values

    def selecter(self, key, value):
        """
        Prende in ingresso il nome del nodo di cui considerare le classi e un valore numerico, restituisce la classe di
        appartenenza di tale valore.

        :param key: Nome del nodo
        :type key: stringa
        :param value: Valore di cui si cerca la classe di appartenenza
        :type value: float

        :return: Classe di appartenenza del valore
        :rtype: stringa
        """

        # print("key: {}".format(key))
        # print("class node: {}".format(self.graph.name_classes_nodes[key]))
        # print("interval: {}".format(self.interval[key]))
        # print("num: {}".format(value))

        if type(value) == bool:
            if value:
                out = "True"
            else:
                out = "False"

        elif type(value) == str:
            out = value

        else:
            for i in range(len(self.interval[key])):
                # print("i selecter: {}".format(i))
                if value < self.interval[key][0]:
                    out = self.graph.name_classes_nodes[key][0]
                elif value >= self.interval[key][i]:
                    out = self.graph.name_classes_nodes[key][i + 1]

        # print("out: {}".format(out))
        return out


class Status:
    """
    Classe usata per memorizzare lo stato dei parametri di interesse del veicolo, tali parametri sono memorizzati nel
    dizionario 'dict_status_var'.

    :param dict_status_var: dizionario con i parametri di interesse {nome_nodo: valore_iniziale}
    :type dict_status_var: dizionario

    **Metodi:**
    """
    def __init__(self, dict_status_var):
        self.dict_status_var = dict_status_var #dizionario con i parametri di interesse
        self.last_update_keys = [] #lista contenente le chiavi dei valori che sono stati aggiornati
        self.last_update_time = 0 #istante di tempo in cui i valori sono stati aggiornati

    def set_value_by_key(self, key, value):
        """
        Metodo usato per settare un valore del dizionario nota la chiave.
        
        :param key: Chiave del dizionario
        :type key: stringa
        :param value: Valore da inserire nel dizionario
        :type value: float
        """
        self.dict_status_var[key] = value

    def get_value_by_key(self, key):
        """
        Metodo usato per accedere ad un valore del dizionario nota la chiave.
        
        :param key: Chiave del dizionario
        :type key: stringa

        :return: Valore del dizionario
        :rtype: float
        """
        return self.dict_status_var[key]

    def get_dict_by_keys(self, key_list):
        """
        Metodo usato per ottere un dizionario contenente parte dei parametri 
        che descrivono lo stato del veicolo, i parametri da restituire 
        devono essere forniti nella lista 'key_list'.
        
        :param key_list: Lista di stringhe contenente i nomi dei parametri che che devono essere restituiti
        :type key_list: lista
        
        :return: Dizionario contenente i parametri di interesse
        :rtype: dizionario
        """
        tmp_dict = {}
        for key in key_list:
            tmp_dict[key] = self.dict_status_var[key]
        return tmp_dict

    def __str__(self):
        string = ""
        string = str(self.dict_status_var) + "\n"
        string = string + "update time: " + str(self.last_update_time) + "\n"
        string = string + "update_keys: " + str(self.last_update_keys) + "\n"
        return str(string)


class StatusBuffer:
    """
    Questa classe implementa un baffer circolare i cui elementi appartengono alla classe 'Status'

    :param status_var_key_list: lista dei nomi de parametri di interesse del veicolo
    :type status_var_key_list: lista
    :param buf_len: lunghezza del buffer (di default pari a 32)
    :type buf_len: int

    **Metodi:**
    """
    def __init__(self, status_var_key_list, buf_len=32):
        """
        Inizializzazione

        :param status_var_key_list: lista dei nomi de parametri di interesse del veicolo
        :type status_var_key_list: lista
        :param buf_len: lunghezza del buffer (di default pari a 32)
        :type buf_len: int
        """
        self.dict_status_var = {}
        self.index = 0
        self.buf_len = buf_len
        self.buf_list = []

        for elem in status_var_key_list:
            self.dict_status_var[elem] = 0

        for i in range(self.buf_len):
            self.buf_list.append(Status(self.dict_status_var.copy()))

    def add_status(self, dict_change, time):
        """
        Metodo che prende in ingresso un dizionario {nome_nodo : valore} con i cambiamenti da apportare allo
        stato corrente rispetto al precendente.
        
        :param dict_change: Dizionario con i cambiamenti da apportare
        :type dict_change: dizionario
        :param time: Istante di tempo in cui viene aggiunto lo stato corrente
        :type time: float
        """
        prev_status = self.buf_list[self.index - 1]
        prev_status_dict = self.buf_list[self.index - 1].dict_status_var

        self.buf_list[self.index].last_update_keys = list(dict_change.keys())
        self.buf_list[self.index].last_update_time = time

        for key in self.buf_list[self.index].dict_status_var.keys():

            if key in dict_change.keys():
                self.buf_list[self.index].set_value_by_key(key, dict_change[key])
            else:
                self.buf_list[self.index].set_value_by_key(key, prev_status_dict[key])

        self.index = (self.index + 1) % self.buf_len

    def get_last_status(self, n=0):
        """
        Metodo usato per accedere agli elementi del buffer. Di default viene restituito
        l'ultimo stato acquisito, con l'argomento 'n' è possibile selezionare
        lo stato n-esimo precedente all'ultimo
        
        :param n: Stato n-esimo precedente all'ultimo
        :type n: int

        :return: Stato selezionato
        :rtype: idsClasses.Status
        """
        # print("last status index: {}".format(str(self.index - num - 1)))
        return self.buf_list[self.index - n - 1]

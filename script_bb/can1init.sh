#!/bin/bash

config-pin p9.24 can
config-pin p9.26 can
#Configurati i Pin 24 e 26 dellheader P9 della beaglebone in modalità CAN

ip link set can1 type can bitrate 500000
ip link set can1 up
#Impostato il bitrate e la tipologia dell'interfaccia can1 ed attivata

#!/bin/bash

#viene assegnato un indirizzo statico all'interfaccia wlan0 che fungerà da access point
ip link set wlan0 down
ip addr add 192.168.100.1/24 dev wlan0
ip link set wlan0 up

#viene avviato dnsmasq che in questo caso verrà utilizzato come server dhcp
systemctl start dnsmasq
#viene avviato hostapd che realizzerà effettivamente l'access point
systemctl start hostapd
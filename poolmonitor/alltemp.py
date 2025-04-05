#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
#
# Customized Home Automation 
#
# Copyright (C) 2016, David Goldfarb
#
# Distributed under the terms of the GNU General Public License
#
# Written by David Goldfarb
#

#-#from w1thermsensor import W1ThermSensor
import time
import RPi.GPIO as GPIO
import socket
import sys
import signal
import json
from math import log10
import os
import paho.mqtt.client as mqtt

try:
  broker = os.environ['MQTTBROKER']
except:
  print("Defaulting to Broker 'localhost'")
  broker = 'localhost'

try:
  port = int(os.environ['MQTTPORT'])
except:
  print("Defaulting to MQTT Broker port 1883")
  port = 1883

# Publish the discovery info for each sensor to homeassistant
def on_connect (client, userdata, flags, rc):
    if rc:
        print("Error connecting to MQTT broker rc "+str(rc))


    print("Connected to MQTT broker, result code "+str(rc))
    payload = {

      "name"          : "poolspatemp",
      "state_topic" : 'home/sensor/poolspatemp/temperature',
      "device_class": 'temperature',
      "unit_of_measurements": "°F",
      "value_template": "{{ value_json.temperature }}",
      "unique_id": "poolspatemp",
      "device": {
        "identifiers": ["poolspatemp"],
        "name": "poolspatemp",
        "model": "Thermistor",
        "manufacturer": "Custom"
      }
    }
    discovery_topic='homeassistant/sensor/poolspatemp/config'
    print("Sending Discovery to MQTT Home Assistant")
    print(discovery_topic)
    print(payload)
    client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True )

    discovery_topic = "homeassistant/switch/spaheater/config"

    # Switch configuration
    payload = {
      "name": "Spa Heater Switch",
      "command_topic": "homeassistant/switch/spaheater/set",
      "state_topic": "homeassistant/switch/spaheater/state",
      "payload_on": "ON",
      "payload_off": "OFF",
      "state_on": "ON",
      "state_off": "OFF",
      "unique_id": "spa_heater_switch_1",
      "device": {
        "identifiers": ["spa_heater_switch_1"],
        "name": "Spa Heater Switch",
        "model": "HS100",
        "manufacturer": "Custom"
      }
    }

    print(discovery_topic)
    print(payload)
    client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True )



print("Establishing MQTT to "+broker+" port "+str(port)+"...")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = None
try:
  client.connect(broker,port)
except:
  print("Connection failed. Make sure broker, port, and user is defined correctly")
  exit(1)


client.loop_start()



# Constants to calculate temp from thermistor
# These three items together will shift the line up and down
# replacted the termister and I believe the nominal value has changed.
THERMISTORNOMINAL=9000.0   
TEMPERATURENOMINAL=25.0   
SERIESRESISTOR=9900.0

# This constant will change the slope of the line
#BCOEFFICIENT= 3600.0
BCOEFFICIENT= 1600.0

OUTCSV="/var/www/html/tempdata.csv"
DEBUG=1

DS18B20_temp_avg=0
ThermistorTemp_F_avg=0
DHT22_temp_avg=0
DHT22_humidity_avg=0
ThermistorRAW_avg=0
PressureRAW_avg=0

def cleanup():
        print("Exiting...")
        GPIO.cleanup()

def signal_handler(signum, frame):
        print("Signal received: ",signum)
        cleanup()
        sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def readadc (adcnum, clockpin, mosipin, misopin, cspin):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
        GPIO.output(cspin, True)

        GPIO.output(clockpin, False)
        GPIO.output(cspin,False)

        commandout = adcnum
        commandout |= 0x18
        commandout <<= 3

        for i in range(5):
                if (commandout & 0x80):
                        GPIO.output(mosipin,True)
                else:
                        GPIO.output(mosipin,False)

                commandout <<= 1
                GPIO.output (clockpin, True)
                GPIO.output (clockpin, False)

        adcout=0
        for i in range(12):
                GPIO.output(clockpin, True)
                GPIO.output(clockpin, False)
                adcout<<=1
                if(GPIO.input(misopin)):
                        adcout |= 0x1

        GPIO.output(cspin,True)

        adcout >>=1
        return adcout


#DS18B20=W1ThermSensor()

r = 0
count=0.0

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# The pins to read the ADC
SPICLK=23
SPIMISO=21
SPIMOSI=19
SPICS=15

GPIO.setup(SPIMOSI,GPIO.OUT)
GPIO.setup(SPIMISO,GPIO.IN)
GPIO.setup(SPICLK,GPIO.OUT)
GPIO.setup(SPICS,GPIO.OUT)

TempADC=0
PressureADC=1

HEADER="TIME,COUNT,HUMIDITY,DHT22_F,DS18B20_F,THERMISTOR,THERMISTOR_RAW,PRESSURE_RAW,PRESSURE_PSI\n"
print(HEADER)

try:
        if os.stat(OUTCSV).st_size > 0:
                f=open(OUTCSV,"a")
        else:
                f=open(OUTCSV,"a")
                f.write(HEADER)
except:
        f=open(OUTCSV,"a")
        f.write("0"+HEADER)

lastminute=int(time.strftime("%M"))

while True:

        # read the DHT22
        r += 1
        count += 1.0

        #DHT22sensor.trigger()
        time.sleep(0.2)

        # Read the DS18B20
#        DS18B20_temp = DS18B20.get_temperature(W1ThermSensor.DEGREES_F)
        DS18B20_temp=70

        # Read the Thermistor
        ThermistorRAW=readadc(TempADC,SPICLK,SPIMOSI,SPIMISO,SPICS)

        if ThermistorRAW==1023.0:
                print("ThermistorRAW did not read correctly")
                ThermistorRAW=512.0

        ThermistorRAW=512.0
        ADvalue=1.0/((1023.0/ThermistorRAW)-1)
        resistance_ratio=(SERIESRESISTOR / THERMISTORNOMINAL) * ADvalue

        steinhart=log10(resistance_ratio)/BCOEFFICIENT
        steinhart=steinhart + (1.0/(TEMPERATURENOMINAL+273.15))
        TempKelvins = 1.0/steinhart
        TempKelvins=293
        ThermistorTemp_F=(TempKelvins-273.20)*9.0/5.0 +32

        # Read the Pressure Sensor
        PressureRAW=readadc(PressureADC,SPICLK,SPIMOSI,SPIMISO,SPICS)
        # 126 raw value=0 PSI   320 raw value = 13PSI   500 raw value = 25PSI
        FilterPressure=(PressureRAW * 0.066854)-8.42246

        #-#DHT22_temp=(DHT22sensor.temperature()*(9.0/5.0))+32.0
        #-#DHT22_humidity=DHT22sensor.humidity()
        DHT22_temp=0
        DHT22_humidity=0

        DS18B20_temp_avg     += DS18B20_temp
        ThermistorTemp_F_avg += ThermistorTemp_F
        DHT22_temp_avg       += DHT22_temp
        DHT22_humidity_avg   += DHT22_humidity
        ThermistorRAW_avg    += ThermistorRAW
        PressureRAW_avg      += PressureRAW

        if (DEBUG==1):
                print( "{},{},{},{},{},{:3.2f},{},{},{}".format(
                        time.strftime("%Y/%m/%d %H:%M:%S"),r,
                        DHT22_humidity,DHT22_temp,
                        DS18B20_temp,ThermistorTemp_F,ThermistorRAW,PressureRAW,FilterPressure))

        minute=int(time.strftime("%M"))

        if (minute != lastminute):
                f.write("{},{},{:3.2f},{:3.2f},{:3.2f},{:3.2f},{:5.2f},{:5.2f},{:3.2f}\n".format(
                        time.strftime("%Y/%m/%d %H:%M:%S"),r, 
                        DHT22_humidity_avg/count, DHT22_temp_avg/count, 
                        DS18B20_temp_avg/count, ThermistorTemp_F_avg/count, ThermistorRAW_avg/count,
                        PressureRAW_avg/count,((PressureRAW_avg/count)*0.066854)-8.42246))
                # Publish to MQTT topic for Home Assistant
                # Round to one significant decimal place
                payload='{:.1f}'.format(ThermistorTemp_F_avg/count)
                payload='{ "temperature" : '+payload+'}'
                topic='home/sensor/poolspatemp/temperature'
                client.publish(topic, payload, qos=0, retain=False  )

                f.flush()

# 2024/07/06 18:29:30,10,0,0,70,67.64,1023,681,37.105114
                t=open("/var/www/html/config/spa_heater_target","r")
                poolctlsocket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                poolctlsocket.connect(('localhost',2222))
                for l in t:
                        if ("#" in l):
                                continue
                        print ("{:3.2f} compared to {:3.2f}\n".format(float(l),ThermistorTemp_F_avg/count))
                        topic='homeassistant/switch/spaheater/state'
                        if float(l) < (ThermistorTemp_F_avg/count):
                                print( "Turn Off Heater")
                                client.publish(topic, "OFF", qos=1, retain=True)
                                poolctlsocket.send(b'{"SpaTempControl":"off"}')
                        else:
                                print( "Turn on Heater")
                                client.publish(topic, "ON", qos=1, retain=True)
                                poolctlsocket.send(b'{"SpaTempControl":"on"}')
                poolctlsocket.close()
                t.close()

                DS18B20_temp_avg=0
                ThermistorTemp_F_avg=0
                DHT22_temp_avg=0
                DHT22_humidity_avg=0
                ThermistorRAW_avg=0
                PressureRAW_avg=0

                count=0
                lastminute=minute


        time.sleep(3) # Overall INTERVAL second polling.

#DHT22sensor.cancel()

#pi.stop()




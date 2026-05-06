#!/usr/bin/python3 -u
# -*- coding: utf-8 -*-
#
# Customized Home Automation 
#
# Copyright (C) 2016,2024 David Goldfarb
#
# Distributed under the terms of the GNU General Public License
#
# Written by David Goldfarb
#

#-#from w1thermsensor import W1ThermSensor
import time
import RPi.GPIO as GPIO
import sys
import signal
import json
import threading

from math import log
import os
import paho.mqtt.client as mqtt

# Constants to calculate temp from thermistor
# These three items together will shift the line up and down
# replacted the termister and I believe the nominal value has changed.
THERMISTORNOMINAL=9550.0   
TEMPERATURENOMINAL=23.88   
SERIESRESISTOR=9900.0

# This constant will change the slope of the line
#BCOEFFICIENT= 3600.0
BCOEFFICIENT= 3950.0

OUTCSV="/var/www/html/tempdata.csv"
DEBUG=1

target_temp  = None
current_temp = None

def on_message(client, userdata, message):
    global target_temp
    topic   = message.topic.split('/')
    command = message.payload.decode('utf-8')
    print("Alltemp mqtt received: ",topic," command: ",command);
    if topic == ['alltemp', 'cmd', 'SpaTempTarget', 'set']:
        target_temp = float(command)
        # Echo back to HA so the number entity shows the current setpoint
        client.publish('alltemp/stat/SpaTempTarget/state', command, qos=1, retain=True)
        evaluate_heater()
    elif topic == ['alltemp', 'stat', 'SpaTempTarget', 'state']:
        # This arrives on startup from the retained state message
        if target_temp is None:
            target_temp = float(command)
            print("Target temp restored from broker: ",target_temp," °F")
            evaluate_heater()

def evaluate_heater():
    print("evaluate_heater: target_temp= ",target_temp,"  current_temp=",current_temp)
    if target_temp is None or current_temp is None:
        return
    command = 'off' if current_temp >= target_temp else 'on'
    client.publish('alltemp/cmd/spaheater/set', command, qos=1, retain=False)

def publish_temperature(temp):
    global current_temp
    current_temp = temp
    payload = '{{"temperature": {:.1f}}}'.format(temp)
    client.publish('alltemp/sensor/poolspatemp/temperature', payload, qos=1, retain=True)
    evaluate_heater()

def on_connect (client, userdata, flags, rc):
    if rc:
        print("Error connecting to MQTT broker rc "+str(rc))
        return

    print("Connected to MQTT broker, result code "+str(rc))
    client.subscribe('alltemp/#')
    print("Waiting for retained target temp from broker...")

def setup_mqtt_devices():

    discovery_topic = 'homeassistant/number/SpaTempTarget/config'
    payload = {
      "name"          : "Spa Temp Target",
      "command_topic" :   'alltemp/cmd/SpaTempTarget/set',
      "state_topic" : 'alltemp/stat/SpaTempTarget/state',
      "device_class": 'temperature',
      "min": 60,
      "max": 105,
      "step": 1,
      "unit_of_measurement": "°F",
      "availability_topic":  "alltemp/availability",
      "unique_id": "spa_temp_target",
      "device": {
        "identifiers": ["spa_temp_target"],
        "name": "Spa Temp Target",
        "model": "HomeAssistant",
        "manufacturer": "alltemp"
      }
    }

    print("Sending Discovery to MQTT Home Assistant")
    print(discovery_topic)
    print(payload)
    client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True )
    client.publish("alltemp/availability","online",qos=1, retain=True )


                        
    discovery_topic = 'homeassistant/sensor/poolspatemp/config'
    payload = {
      "name"          : "poolspatemp",
      "state_topic" : 'alltemp/sensor/poolspatemp/temperature',
      "device_class": 'temperature',
      "unit_of_measurement": "°F",
      "value_template": "{{ value_json.temperature }}",
      "unique_id": "poolspatemp",
      "device": {
        "identifiers": ["poolspatemp"],
        "name": "poolspatemp",
        "model": "Thermistor",
        "manufacturer": "alltemp"
      }
    }
    print("Sending Discovery to MQTT Home Assistant")
    print(discovery_topic)
    print(payload)
    client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True )

    discovery_topic = "homeassistant/switch/spaheater/config"

    # Switch configuration
    payload = {
      "name": "Spa Heater Switch",
      "command_topic": "alltemp/cmd/spaheater/set",
      "state_topic": "alltemp/stat/spaheater/state",
      "payload_on": "on",
      "payload_off": "off",
      "state_on": "on",
      "state_off": "off",
      "unique_id": "spa_heater_switch_1",
      "device": {
        "identifiers": ["spa_heater_switch_1"],
        "name": "Spa Heater Switch",
        "model": "HS100",
        "manufacturer": "alltemp"
      }
    }

    print(discovery_topic)
    print(payload)
    client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True )



def mqtt_listener():
    global client
    # Use environment variables to find the MQTT broker if they exist
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


    print("Establishing MQTT to "+broker+" port "+str(port)+"...")

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    try:
      client.connect(broker,port)
    except:
      print("Connection failed. Make sure broker, port, and user is defined correctly")
      exit(1)

    # Publish the discovery info for each sensor to homeassistant
    setup_mqtt_devices()

    client.loop_start()




shutdown_event = threading.Event()

def cleanup():
    print("Exiting...")
    GPIO.cleanup()

def signal_handler(signum, frame):
    print("Signal received: ",signum)
    shutdown_event.set()  # Signal all threads to stop

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
        print("adcout",adcnum," from readadc: ",adcout)
        return adcout

def monitor_temps():
    global current_temp
    #DS18B20=W1ThermSensor()
    DS18B20_temp_avg=0
    ThermistorTemp_F_avg=0
    DHT22_temp_avg=0
    DHT22_humidity_avg=0
    ThermistorRAW_avg=0
    PressureRAW_avg=0

    
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
    
    while not shutdown_event.is_set():
    
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

        thermistor_resistance = SERIESRESISTOR * ThermistorRAW / (1023.0 - ThermistorRAW)
        steinhart = log(thermistor_resistance / THERMISTORNOMINAL) / BCOEFFICIENT
        steinhart = steinhart + (1.0 / (TEMPERATURENOMINAL + 273.15))
        TempKelvins = 1.0 / steinhart
        ThermistorTemp_F = (TempKelvins - 273.15) * 9.0 / 5.0 + 32

#        ThermistorRAW=512.0
#        ADvalue=1.0/((1023.0/ThermistorRAW)-1)
#        resistance_ratio=(SERIESRESISTOR / THERMISTORNOMINAL) * ADvalue
#        thermistor_resistance = SERIESRESISTOR * ThermistorRAW / (1023.0 - ThermistorRAW)
#
#        steinhart=log10(resistance_ratio)/BCOEFFICIENT
#        steinhart=steinhart + (1.0/(TEMPERATURENOMINAL+273.15))
#        TempKelvins = 1.0/steinhart
#        TempKelvins=293
#        ThermistorTemp_F=(TempKelvins-273.15)*9.0/5.0 +32

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
            current_temp=ThermistorTemp_F_avg/count
            publish_temperature(current_temp) 
            f.flush()

# 2024/07/06 18:29:30,10,0,0,70,67.64,1023,681,37.105114

            DS18B20_temp_avg=0
            ThermistorTemp_F_avg=0
            DHT22_temp_avg=0
            DHT22_humidity_avg=0
            ThermistorRAW_avg=0
            PressureRAW_avg=0

            count=0
            lastminute=minute


        time.sleep(3) # Overall INTERVAL second polling.
    print("monitor_temps exiting")
    cleanup() 
#DHT22sensor.cancel()

#pi.stop()


if not 'alltemp' in sys.modules:

    # Create a thread for the TCP listener
    monitor_thread = threading.Thread(target=monitor_temps, daemon=True)
    monitor_thread.start()

    # Create a thread for the MQTT listener
    mqtt_thread = threading.Thread(target=mqtt_listener, daemon=True)
    mqtt_thread.start()

    # Main thread waits here until signal received
    shutdown_event.wait()
    print("Exiting...")
    try:
        client.publish('alltemp/availability', 'offline', qos=1, retain=True)
        client.disconnect()
    except Exception as e:
        print("Could not publish offline status:",e)

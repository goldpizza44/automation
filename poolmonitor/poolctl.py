#!/usr/bin/python3 -u
#EMACS_MODES: notabs,tabstop=8
#
# Customized Home Automation 
#
# Copyright (C) 2016, David Goldfarb
#
# Distributed under the terms of the GNU General Public License
#
# Written by David Goldfarb
#

import RPi.GPIO as GPIO
import time
import socket
import sys
import threading
import json
import paho.mqtt.client as mqtt

global DEBUG
DEBUG=1

# Set the GPIO pins to be used for the binary selectors
# A0 -> A7  goto the upper Relay board which is negative logic...False = activate relay
# A8 -> A15 goto the lower Relay board which is positive logic...True  = activate relay
# Associate the BCM GPIO numbers to the RELAY positions.  Also noted are the pinouts on the header
# (both main header and P5 header)
A0=7  #pin26   -- Valve 1 (Return Spray) CW
A1=8  #pin24   -- Valve 1 (Return Spray) CCW
A2=25 #pin22   -- Valve 2 (BubblerReturnSpray) CW
A3=24 #pin18   -- Valve 2 (BubblerReturnSpray) CCW
A4=23 #pin16   -- Valve 3 (SpaPool) CW
A5=18 #pin12   -- Valve 3 (SpaPool) CCW
A6=15 #pin10   -- Pump Speed 1
A7=14 #pin8    -- Pump Speed 2

A8=28  #P5pin3 -- Valve 5 (MainDrainSpaPool) CW
A9=29  #P5pin4 -- Valve 5 (MainDrainSpaPool) CCW
A10=30 #P5pin5 -- Valve 4 (SpaFloorJets) CW
A11=31 #P5pin6 -- Valve 4 (SpaFloorJets) CCW
A12=3  #pin5   -- Pool Light
A13=2  #pin3   -- Main Pump Power
A14=27 #pin13  -- Pool Heater
A15=17 #pin11  -- Pump Speed 3

# GPIOs 22,10,9,11 are Digital inputs from the ADC that reads Pressure and Temp info.
# These are on Header pins 15,19,21,23

# Associate the above relay numbers (0 -> 15)
poollist={
        'PoolLight':12,
        'MainPump':13,
        'SpaHeater':14,
        'PumpSpeed1':6,
        'PumpSpeed2':7,
        'PumpSpeed3':15,
        'SpaTempTarget':'/var/www/html/config/spa_heater_target'
}
poolcolor='off'

class valve():
        def __init__(self,num,name,cw_relay,ccw_relay):
                self.num=num
                self.name=name
                self.cw_relay=int(cw_relay)
                self.ccw_relay=int(ccw_relay)

        def get_CWrelay(self):        return self.cw_relay
        def get_CCWrelay(self): return self.ccw_relay

# Valve Configs are in a separate file
# CONFIG columns
VALVENUM=0
VALVENAME=1
VALVE_CW=2
VALVE_CCW=3

global valvelist
valvelist={}
f=open("/var/www/html/config/valve_config","r")
for l in f:
        if ("#" in l):
                continue
        data=l.split()
#        data=[ d.decode('UTF-8') for d in data ]
        if(len(data)>=4):
                valvelist[data[VALVENAME]]=valve(data[VALVENUM],data[VALVENAME],data[VALVE_CW],data[VALVE_CCW])

f.close()



# All the relays are setup as OUTGOING signals
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(A0, GPIO.OUT)
GPIO.setup(A1, GPIO.OUT)
GPIO.setup(A2, GPIO.OUT)
GPIO.setup(A3, GPIO.OUT)
GPIO.setup(A4, GPIO.OUT)
GPIO.setup(A5, GPIO.OUT)
GPIO.setup(A6, GPIO.OUT)
GPIO.setup(A7, GPIO.OUT)
GPIO.setup(A8, GPIO.OUT)
GPIO.setup(A9, GPIO.OUT)
GPIO.setup(A10, GPIO.OUT)
GPIO.setup(A11, GPIO.OUT)
GPIO.setup(A12, GPIO.OUT)
GPIO.setup(A13, GPIO.OUT)
GPIO.setup(A14, GPIO.OUT)
GPIO.setup(A15, GPIO.OUT)

print ( "GPIO SETUP COMPLETE" )

def activateRELAY(relay,setting="False",read_set="set"):

        # These are negative logic.
        if(relay==0): RELAY=A0;        setting=not setting
        if(relay==1): RELAY=A1; setting=not setting
        if(relay==2): RELAY=A2; setting=not setting
        if(relay==3): RELAY=A3; setting=not setting
        if(relay==4): RELAY=A4; setting=not setting
        if(relay==5): RELAY=A5; setting=not setting
        if(relay==6): RELAY=A6; setting=not setting
        if(relay==7): RELAY=A7; setting=not setting

        # These are positive logic
        if(relay==8):  RELAY=A8
        if(relay==9):  RELAY=A9
        if(relay==10): RELAY=A10
        if(relay==11): RELAY=A11
        if(relay==12): RELAY=A12
        if(relay==13): RELAY=A13
        if(relay==14): RELAY=A14
        if(relay==15): RELAY=A15

        if (read_set == "set"):
                return GPIO.output(RELAY,setting)
        else:
                V=GPIO.input(RELAY)
                # Adjust for negative logic 
                if relay <= 7: V=not V
                if DEBUG: print ( "Reading RELAY",relay,"GPIO: ",RELAY,"Value: ",V )
                return V



 


global positionlist
global featurelist
global featureposition
positionlist={}
featurelist={}
featureposition={}
column=[]
SpaHeater='off'

f=open("/var/www/html/config/possible_positions","r")
for l in f:
        if ("#" in l):
                continue

        data=l.split()
        if (len(data)==0):
                # Blank line
                continue

        # This makes the table flexible so that we can have any number of valves
        # The first 'n' columns should be the setting for each valve in degrees
        # and the last column will be the features that are 'on' with this setting
        # the 'VALVECOLUMNS:' tag defines which valve each of the columns represents.
        # These strings will match those in 'valve_config'
        if data[0]=='VALVECOLUMNS:':
                for i in range(1,len(data)):
                        column.append(data[i])

                NUMBEROFVALVES=len(data)-1
                continue
        elif data[0]=='FEATURES:':
                pass
        else:
                v=[]
                vpos1={}
                for i in range(0,NUMBEROFVALVES):
                        v.append(int(data[i]))
                        vpos1[column[i]]=data[i]

                vpos=tuple(v)
                flist=data[NUMBEROFVALVES].split(',')
                # Convert to Unicode.  This is done because incoming json is unicode.
#                flist=[ feature.decode('UTF-8') for feature in flist ]
                positionlist[vpos]=flist
                featureposition[tuple(flist)]=vpos1

                for feature in flist:
                        if feature in featurelist: featurelist[feature].append(vpos)
                        else:
                                featurelist[feature] = [ vpos ]
                
f.close()

# These are the number of seconds that a valve will turn to get to a specific
# position.  The first number is the degrees and second is seconds
# The valves turn about 4.75 degrees per second or about 210 milliseconds per degree
def turnValve(valvename,result,direction,degrees_to_turn=False,seconds_to_turn=False):
        # Determine the degrees_to_turn (CW or CCW).  Negative is CCW

        if (direction < 0):
                RELAY=valvelist[valvename].get_CWrelay()
        elif (direction > 0):
                RELAY=valvelist[valvename].get_CCWrelay()
        else:
                # No change, return
                result[valvename]='NoChange'
                return
        if degrees_to_turn:
                seconds_to_turn=degrees_to_turn * 0.210


        if DEBUG: print ( "Activating RELAY "+str(RELAY)+" for "+str(seconds_to_turn)+" seconds" )
        activateRELAY(RELAY,True)
        time.sleep(seconds_to_turn)
        if DEBUG: print ( "Deactivating RELAY "+str(RELAY) )
        activateRELAY(RELAY,False)
        result[valvename]='Success'


SECS={        45:9.5, 90:19, 135:28.5, 180:40,  }

def setValve(valvename,degrees_to_turn,result):

        # Determine the degrees_to_turn (CW or CCW).  Negative is CCW

        if (degrees_to_turn > 0):
                RELAY=valvelist[valvename].get_CCWrelay()
        elif (degrees_to_turn < 0):
                RELAY=valvelist[valvename].get_CWrelay()
                degrees_to_turn=0-degrees_to_turn
        else:
                # No change, return
                result[valvename]='NoChange'
                return 

        if (degrees_to_turn in SECS):
                if DEBUG: print ( "Activating RELAY "+str(RELAY)+" for "+str(SECS[degrees_to_turn])+" seconds" )
                activateRELAY(RELAY,True)
                time.sleep(SECS[degrees_to_turn])
                if DEBUG: print ( "Deactivating RELAY "+str(RELAY) )
                activateRELAY(RELAY,False)
                result[valvename]='Success'
        elif degrees_to_turn==1:
                print ( "RELAY: "+str(RELAY)+" Don't care value of -1...skipping" )
        else:
                result[valvename]='InvalidDegrees '+str(degrees_to_turn)
                print ( "Invalid Degrees "+str(degrees_to_turn)+" ... No change made" )

        return


                
def getValveList():
        valvesettings={}
        f=open("/var/www/html/config/valve_settings","r")
        for l in f:
                data=l.split()
                if(len(data) == 2):
                        valvesettings[data[0]]=int(data[1])

        f.close()

        return valvesettings

def setValveList(valveChangeList):

        valvesettings=getValveList()

        valveThread={}
        valveResult={}

        if DEBUG: print ( "valveChangeList",valveChangeList )
        for valve in valveChangeList:
                if(not(valve in valveThread)):
                        degrees_to_turn=valveChangeList[valve]-valvesettings[valve]
                        valveResult[valve]='Unknown'
                        try:
                                valveThread[valve]=threading.Thread(target=setValve, args=(valve,degrees_to_turn,valveResult,))
                                valveThread[valve].start()
                        except:
                                print ( "Error:  unable to start Thread for valve "+valve )
                else:
                        print ( "Can't change Valve "+valve+" to two different settings at the same time" )

        # The valves should be turning now...Wait for them to finish.
        # Join each thread for a minimum of 45 secs
        for v in valveThread:
                valveThread[v].join(45)

        for v in valveResult:
                if(valveResult[v]=='Unknown'):
                        # For some reason the thread did not finish in 40 seconds
                        # try to kill the thread
                        print ( "Thread for "+v+" had Result Unknown" )
                if(valveResult[v]=='Success'):        valvesettings[v]=valveChangeList[v]

        # For the valve changes that were successful, write them back to the file
        f=open("/var/www/html/config/valve_settings","w")
        for v in valvesettings:        f.write(v+'        '+str(valvesettings[v])+'\n')
        f.close()

        return getValveList()

def equalSetting(setting1,setting2):
        for i in range(0,3):
                if(setting1[i] != -1 and setting2[i]!= -1 and setting1[i]!=setting2[i]):
                        return False
        return True


def getFeatureList():

        valvesettings={}
        f=open("/var/www/html/config/valve_settings","r")
        for l in f:
                data=l.split()
                if(len(data) == 2):
                        valvesettings[data[0]]=int(data[1])

        f.close()

        currentPos=(valvesettings['SpaFloorJets'],valvesettings['SpaPool'],valvesettings['BubblerReturnSpray'],valvesettings['ReturnSpray'])

        for vpos in positionlist:
                if equalSetting(currentPos,vpos):
                        newFeatures=positionlist[vpos]        

        # newFeatures contains the current features that are on
        
        fl={}
        for feature in featurelist:
                if feature in newFeatures: fl[feature]="on"
                else: fl[feature]="off"                

        return fl

def setFeatureList(featureChangeList):

        if DEBUG: print ( "featureChangeList",featureChangeList )

        # Get the current list
        newFeatures=getFeatureList()
        print ( "newFeatures",newFeatures )
        # Update the current list with the requested changes
        for feature in featureChangeList:
                newFeatures[feature]=featureChangeList[feature]

        # Convert the set to a list of features that are on
        feat=[ feat for feat in newFeatures if newFeatures[feat]=='on' ]

        # Now we have a list of features that should be on (feat).  Search
        # featureposition for the matching list so that which will tell us the 
        # valve settings
        for ftuple in featureposition:
                if set(ftuple) == set(feat):
                        # Remove the dont cares
                        fp=featureposition[ftuple]
                        for f,d in list(fp.items()):
                                if d == -1: del fp[f]
                        try:
                                setValveList(fp )
                        except Exception as e:
                                print ( "setValveList exception: "+str(e) )

                        break

        return newFeatures


def setPoolList(poolChangeList):
        global poolcolor
        for p in poolChangeList:

                if p == "SpaTempTarget":
                        t=open(poollist[p],"w")
                        t.write(str(poolChangeList[p]))
                        t.close()
                if poolChangeList[p]=='on':
                        if DEBUG: print ( "Activating RELAY "+str(poollist[p]) )
                        activateRELAY(poollist[p],True)
                elif poolChangeList[p]=='off':
                        if p == "PoolLight": poolcolor='off'
                        if DEBUG: print ( "Deactivating RELAY "+str(poollist[p]) )
                        activateRELAY(poollist[p],False)

        return getPoolList()


def getPoolList():
        global SpaHeater
        poolsettings={}
        for p in poollist:
                if p == 'PoolLight':
                        poolsettings[p]=poolcolor
                elif p == 'SpaTempTarget':
                        t=open(poollist[p],"r")
                        for l in t:
                                if ("#" in l): continue
                                poolsettings[p]=int(l)
                        t.close()
                elif p == 'MainPump':
                        # Variable speed pump read speed...
                        if DEBUG: print ( "Checking Pump Speed" )
                        if   activateRELAY(poollist['PumpSpeed3'],read_set="read"):
                                if DEBUG: print ( "Setting speed to 500" )
                                poolsettings[p]='500'
                        elif activateRELAY(poollist['PumpSpeed2'],read_set="read"):
                                if DEBUG: print ( "Setting speed to 1250" )
                                poolsettings[p]='1250'
                        elif activateRELAY(poollist['PumpSpeed1'],read_set="read"):
                                if DEBUG: print ( "Setting speed to 2750" )
                                poolsettings[p]='2750'
                        elif activateRELAY(poollist['MainPump'],read_set="read"):
                                if DEBUG: print ( "Setting speed to AUTO" )
                                poolsettings[p]='AUTO'
                        else:
                                poolsettings[p]='0'
                elif p == 'SpaHeater':
                        # Use the global variable instead of the relay setting
                        poolsettings[p]=SpaHeater
                elif activateRELAY(poollist[p],read_set="read"):
                        poolsettings[p]='on'
                else:
                        poolsettings[p]='off'

        return poolsettings

def cyclePoolLight(count):
        activateRELAY(poollist['PoolLight'],True)

        for i in range(count-1):
                activateRELAY(poollist['PoolLight'],False)
                time.sleep(0.25)
                activateRELAY(poollist['PoolLight'],True)
                time.sleep(0.25)

def poolLight(color):
        global poolcolor

        if color=="one":
                cyclePoolLight(1)
        elif color=="white_green_blue_magenta"  or color=="SAM":
                cyclePoolLight(2)
        elif color=="red_white_green_blue"      or color=="Party":
                # Color cycles fast
                cyclePoolLight(3)
        elif color=="Romance":
                # Color cycles slow
                cyclePoolLight(4)
        elif color=="blue_green"                or color=="Caribbean":
                # Color cycles medium
                cyclePoolLight(5)
        elif color=="red_white_blue"            or color=="American":
                cyclePoolLight(6)
        elif color=="orange_red_magenta"        or color=="Cal_Sunset":
                cyclePoolLight(7)
        elif color=="magenta_blue_green_yellow" or color=="Royal":
                cyclePoolLight(8)
        elif color=="Blue":
                cyclePoolLight(9)
        elif color=="Green":
                cyclePoolLight(10)
        elif color=="Red":
                cyclePoolLight(11)
        elif color=="White":
                cyclePoolLight(12)
        elif color=="Magenta":
                cyclePoolLight(13)
        elif color=="HOLD":
                cyclePoolLight(14)
        elif color=="RECALL":
                cyclePoolLight(15)
        
        poolcolor=color

def ValveAction(valveJSON):
        global SpaHeater
        try:
                result="None"
                settinglist={}
                print ('valveJSON=', valveJSON )
                for settingType in valveJSON:
                        print('settingType=',settingType)
                        if settingType == "valveSetting":
                                # Remove valves that have invalid names
                                valveChangeList=valveJSON["valveSetting"]
                                valveChangeList={v:valveChangeList[v] for v in valveChangeList if v in valvelist}
                                settinglist["valves"]=setValveList(valveChangeList)
                        elif settingType == "valveTuning":
                                # Change the valves by turning by seconds or degrees, but no update to valve_settings table
                                result={}
                                valveChange=valveJSON["valveTuning"]
                                valve=False
                                for v in valveChange:
                                        if v in valvelist:
                                                valve=v
                                                break
                                if not valve:
                                        print("ERROR: valve not valid")
                                        result='{ "error":"ERROR: valve not valid" }'
                                        return(result)
                                changeInSecs=True if "type" in valveChange and valveChange["type"]=="secs" else False
                                direction=-1 if ("direction" in valveChange and valveChange["direction"]=="ccw") else 1
                                if changeInSecs:
                                        print("Tuning "+valve+" by Turning in direction "+str(direction)+" for "+str(valveChange[valve])+" seconds")
                                        turnValve(valve,result,direction,seconds_to_turn=valveChange[valve])
                                else:
                                        print("Tuning "+valve+" by Turning in direction "+str(direction)+" for "+str(valveChange[valve])+" degrees")
                                        turnValve(valve,result,direction,degrees_to_turn=valveChange[valve])
                                settinglist={"valve":valveChange[valve],"direction":direction,"changeInSecs":changeInSecs}
                        elif settingType == "featureSetting":
                                featureChangeList=valveJSON["featureSetting"]
                                featureChangeList={f:featureChangeList[f] for f in featureChangeList if f in featurelist}
                                settinglist["features"]=setFeatureList(featureChangeList)
                        elif settingType == "getSettings":
                                if valveJSON["getSettings"]=="all":
                                        settinglist["features"]=getFeatureList()
                                        settinglist["valves"]=getValveList()
                                        settinglist["pool"]=getPoolList()
                                elif valveJSON["getSettings"]=="valves":
                                        settinglist["valves"]=getValveList()
                                elif valveJSON["getSettings"]=="features":
                                        settinglist["features"]=getFeatureList()
                        elif settingType == "poolSetting":
                                poolChangeList=valveJSON["poolSetting"]
                                poolChangeList={p:poolChangeList[p] for p in poolChangeList if p in poollist}
                                print ( poolChangeList )
                                if "SpaHeater" in poolChangeList:
                                        SpaHeater=poolChangeList["SpaHeater"]
                                print ( "SpaHeater = "+SpaHeater )
                                settinglist["pool"]=setPoolList(poolChangeList)
                        elif settingType == "SpaTempControl":
                                if SpaHeater == "on":
                                        poolChangeList=valveJSON["SpaTempControl"]
                                        if valveJSON["SpaTempControl"] == "on":
                                                poolChangeList={"SpaHeater":"on"}
                                        else:
                                                poolChangeList={"SpaHeater":"off"}
                                        settinglist["pool"]=setPoolList(poolChangeList)
                                else:
                                        print ( 'Ignoring SpaTempControl because Spa Not On' )

                        elif settingType == "poolColor":
                                poolLight(valveJSON["poolColor"]["Color"])
                                print ( "Main poolcolor="+poolcolor )
                                settinglist["pool"]=getPoolList()

                        result=json.dumps(settinglist)


        except Exception as e:
                result=json.dumps({ "error": str(e) } )
                print ( "ngsetValveList exception: " ,e)

        return(result)


try:
        broker = os.environ['MQTTBROKER']
except:
        print("Defaulting to Broker 'poolmonitor.goldfarbs.net'")
        broker = 'poolmonitor.goldfarbs.net'
  
try:
        port = int(os.environ['MQTTPORT'])
except:
        print("Defaulting to MQTT Broker port 1883")
        port = 1883

poolctltopic='poolctl/#'

def on_connect (client, userdata, flags, rc):
        # Set up MQTT subscription
        if rc:
                print("Error connecting to MQTT broker rc "+str(rc))


        print("Connected to MQTT broker, result code "+str(rc))
        client.subscribe(poolctltopic)
#
# POOL DEVICES:
# PoolPump -- 4 different settings (slow med high off) (relay command to x10mqtt)
# PoolHeater -- On Off
# PoolValves -- Direct Control of valves individually
# PoolFeatures -- valves are set based on commands
# PoolLight -- Color Select
# SpaTemp -- degrees

def setup_mqtt_devices():
        discovery_topic='homeassistant/select/PoolPump/config'
        payload = {
                "name"          : 'PoolPump',
                "command_topic" : 'poolctl/cmd/PoolPump/set',
                "state_topic"  : 'poolctl/stat/PoolPump/state',
                "options": [ "off", "slow", "med", "high" ],
                "unique_id": 'PoolPump',
                "device": {
                        "identifiers": ['PoolPump'],
                        "name": 'PoolPump',
                        "model": "Pump",
                        "manufacturer": "RaspberryPi"
                }
        }

        print(discovery_topic)
        print(payload)
        mqtt_client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True  )

        discovery_topic='homeassistant/select/PoolLight/config'
        payload = {
                "name"          : 'PoolLight',
                "command_topic" : 'poolctl/cmd/PoolLight/set',
                "state_topic"  : 'poolctl/stat/PoolLight/state',
                "options": [ "Off", "Blue","Green","Red","White","Magenta","Romance","Blue_Green","Red_White_Blue","Orange_Red_Magenta","Red_White_Green_Blue","White_Green_Blue_Magenta","Magenta_Blue_Green_Yellow" ],
                "unique_id": 'PoolLight',
                "device": {
                        "identifiers": ['PoolLight'],
                        "name": 'PoolLight',
                        "model": "MultiColorLight",
                        "manufacturer": "RaspberryPi"
                }
        }

        print(discovery_topic)
        print(payload)
        mqtt_client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True  )

                                         
def on_message(client, userdata, message):

        # Determine the device from the topic
        # Topics are cmdtopic/dev, e.g. 'x10/cmd/A1'
        # So the last part is the device we want to control

        command = str(message.payload.decode('utf-8'))
        print("MQTT Message received: "+command)

        try:
                valveJSON = json.loads(command)
                print("Received: "+message.topic+" "+json.dumps(valveJSON))
                result=ValveAction(valveJSON)
                mqtt_client.publish(stattopic,result,retain=True)
        except:
                print("Exception in processing")
                print(message)







def mqtt_listener():
        global mqtt_client
        mqtt_client = mqtt.Client()
        mqtt_client.on_message = on_message
        mqtt_client.on_connect = on_connect

        # Connect to the MQTT broker
        print("Connecting to broker: "+broker+":"+str(port))
        mqtt_client.connect(broker,port)

        setup_mqtt_devices()
        # Start the loop
        mqtt_client.loop_forever()

def tcp_listener():
        sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        server_address=('0.0.0.0',2222)
        sock.bind(server_address)

        sock.listen(1)

        while True:
                # Wait for a connection
                connection, client_address=sock.accept()
                if (client_address[0] != '172.16.2.254' and client_address[0] != 'localhost' and client_address[0] != '127.0.0.1' ):
                        print ( "connection from unknown IP "+client_address[0] )
                        connection.close()
                        continue

                try:
                        # Receive the data in small chunks and retransmit it
                        valvechanges=b""
                        while True:
                                data = connection.recv(16)

                                if data:        valvechanges+=data
                                else:                break

                except Exception as e: 
                        result='{"Error":"Exception Receiving data: '+str(e)+'"}'


                try:
                        valveJSON=json.loads(valvechanges.decode('utf-8'))
                except Exception as e:
                        result='{"Error":"Invalid JSON"}'

                try:
                        result = ValveAction(valveJSON)
                except Exception as e:
                        result='{"Error": "Exception during ValveAction '+ str(e)+ '" }'

                print ( result )

                # Clean up the connection
                connection.sendall((result+'\n').encode('utf-8'))
                connection.close()

# Only start the valve server if we are called standalone
if not 'poolctl' in sys.modules: 
        if activateRELAY(poollist['SpaHeater'],read_set="read"):
                SpaHeater='on'
        else:
                SpaHeater='off'

        # Set the poolcolor to a RECALL on start
        poolLight('RECALL')
 

        # Create a thread for the TCP listener
        tcp_thread = threading.Thread(target=tcp_listener)
        tcp_thread.start()

        # Create a thread for the MQTT listener
        mqtt_thread = threading.Thread(target=mqtt_listener)
        mqtt_thread.start()

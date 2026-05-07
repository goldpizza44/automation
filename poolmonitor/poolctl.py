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
import os
import paho.mqtt.client as mqtt
import datetime

global DEBUG
DEBUG=1

# Set the GPIO pins to be used for the binary selectors
# A0 -> A7  goto the upper Relay board which is negative logic...False = activate relay
# A8 -> A15 goto the lower Relay board which is positive logic...True  = activate relay
# Associate the BCM GPIO numbers to the RELAY positions.  Also noted are the pinouts on the header
# (both main header and P5 header)
A0=8  #pin24   -- Valve 1 (Return Spray) CCW
A1=7  #pin26   -- Valve 0 (Return Spray) CW
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

        def get_CWrelay(self):  return self.cw_relay
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

print("GPIO SETUP COMPLETE")

def activateRELAY(relay, setting="False", read_set="set"):
        # These are negative logic.
        if(relay==0): RELAY=A0;  setting=not setting
        if(relay==1): RELAY=A1;  setting=not setting
        if(relay==2): RELAY=A2;  setting=not setting
        if(relay==3): RELAY=A3;  setting=not setting
        if(relay==4): RELAY=A4;  setting=not setting
        if(relay==5): RELAY=A5;  setting=not setting
        if(relay==6): RELAY=A6;  setting=not setting
        if(relay==7): RELAY=A7;  setting=not setting

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
                return GPIO.output(RELAY, setting)
        else:
                V=GPIO.input(RELAY)
                # Set to Boolean Value and Adjust for negative logic
                V=True if V else False
                if relay <= 7: V=not V
                if DEBUG: print("Reading RELAY", relay, "GPIO: ", RELAY, "Value: ", V)
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
                positionlist[vpos]=flist
                featureposition[tuple(flist)]=vpos1

                for feature in flist:
                        if feature in featurelist:
                                featurelist[feature].append(vpos)
                        else:
                                featurelist[feature] = [vpos]

f.close()

# ------------------------------------------------------------------
# In-memory valve position state.
# This is the authoritative position during runtime.
# valve_settings file is only written on shutdown or explicit request.
# valve_positions_lock protects reads/writes of valve_positions dict.
# ------------------------------------------------------------------
valve_positions = {}       # {valvename: current_degrees}
valve_positions_lock = threading.Lock()

def loadValvePositions():
        """Load valve positions from file into memory at startup."""
        global valve_positions
        settings = {}
        with open("/var/www/html/config/valve_settings","r") as f:
                for l in f:
                        data=l.split()
                        if len(data) == 2:
                                settings[data[0]] = int(data[1])
        with valve_positions_lock:
                valve_positions = settings
        print("Loaded valve positions: ", settings)

def getValvePosition(valvename):
        """Get current in-memory position of a single valve."""
        with valve_positions_lock:
                return valve_positions.get(valvename, 0)

def setValvePosition(valvename, degrees):
        """Update in-memory position of a single valve."""
        with valve_positions_lock:
                valve_positions[valvename] = int(degrees)

def getValveList():
        """Return a copy of all current valve positions."""
        with valve_positions_lock:
                return dict(valve_positions)

def writeValveSettings():
        """Persist current in-memory positions to the valve_settings file."""
        with valve_positions_lock:
                positions = dict(valve_positions)
        with open("/var/www/html/config/valve_settings","w") as f:
                for v in positions:
                        f.write(v+'        '+str(positions[v])+'\n')
        print("valve_settings written to disk")


# ------------------------------------------------------------------
# Per-valve worker threads.
# Each valve has its own thread and command queue so that commands
# for different valves run in parallel, while commands for the
# same valve are serialized (the valve can only do one thing at a time).
# ------------------------------------------------------------------

# How long to wait after receiving a command before starting to move,
# to allow scene commands for other valves to arrive and start together.
VALVE_COLLECT_WINDOW_SECS = 0.15

# {valvename: queue.Queue()}  -- populated in start_valve_threads()
valve_threads = {}
valve_queues  = {}

# Tracks all pending commands so we can write the file after everyone finishes.
# pending_count is decremented by each valve thread when its move completes.
pending_lock  = threading.Lock()
pending_count = 0
pending_done  = threading.Event()   # set when pending_count reaches 0

# This is a table of degrees to seconds that the actuator needs to be on.
SECS={     5: 1.05,  10: 2.10,  15: 3.15,  20: 4.20,  25: 5.25,  30: 6.30,  35: 7.35,  40: 8.40,  45: 9.50,
          50: 10.55,  55: 11.60,  60: 12.75,  65: 13.80,  70: 14.85,  75: 15.90,  80: 16.95,  85: 18.00,  90: 19.00,
          95: 20.05, 100: 21.10, 105: 22.15, 110: 23.20, 115: 24.25, 120: 25.30, 125: 26.35, 130: 27.40, 135: 28.50,
         140: 29.70, 145: 30.90, 150: 32.10, 155: 33.30, 160: 34.50, 165: 35.70, 170: 36.90, 175: 38.50, 180: 40.00}

def _move_valve(valvename, degrees_to_turn):
        """Physically move a valve by degrees_to_turn (negative = CW, positive = CCW)."""
        if degrees_to_turn == 0:
                print("{}: no change needed".format(valvename))
                return True

        if degrees_to_turn > 0:
                RELAY = valvelist[valvename].get_CCWrelay()
        else:
                RELAY = valvelist[valvename].get_CWrelay()
                degrees_to_turn = -degrees_to_turn

        if degrees_to_turn not in SECS:
                if degrees_to_turn == 1:
                        print("{}: don't care value of 1, skipping".format(valvename))
                        return True
                print("{}: invalid degrees {} -- no change made".format(valvename, degrees_to_turn))
                return False

        secs = SECS[degrees_to_turn]
        print("{}: activating RELAY {} for {} secs".format(valvename, RELAY, secs))
        activateRELAY(RELAY, True)
        time.sleep(secs)
        activateRELAY(RELAY, False)
        print("{}: done".format(valvename))
        return True

def _decrement_pending(valvename):
        """Decrement the shared pending counter; write file when all done."""
        global pending_count
        with pending_lock:
                pending_count -= 1
                remaining = pending_count
        print("{}: pending_count now {}".format(valvename, remaining))
        if remaining == 0:
                writeValveSettings()
                pending_done.set()

def valve_thread_worker(valvename, q):
        """
        Dedicated worker thread for one valve.
        Sits waiting for (target_degrees, done_event) tuples.
        Always processes the latest queued target -- if multiple
        commands arrive while a move is in progress, only the
        most recent target matters.
        """
        while True:
                item = q.get()
                if item is None:
                        break   # shutdown

                target_degrees, done_event = item

                # Drain any additional commands that arrived while we were
                # waiting -- take the latest target only.
                while not q.empty():
                        try:
                                next_item = q.get_nowait()
                                if next_item is None:
                                        q.put(None)   # re-queue shutdown signal
                                        break
                                # decrement pending for the superseded command
                                _, superseded_event = next_item
                                _decrement_pending(valvename)
                                superseded_event.set()
                                target_degrees, done_event = next_item
                        except:
                                break

                current = getValvePosition(valvename)
                degrees_to_turn = target_degrees - current
                # Round to nearest 5 degrees
                degrees_to_turn = round(degrees_to_turn / 5) * 5
                # Take the short way round
                if degrees_to_turn > 180:
                        degrees_to_turn = (360 - degrees_to_turn) * -1
                elif degrees_to_turn < -180:
                        degrees_to_turn = (360 + degrees_to_turn)

                success = _move_valve(valvename, degrees_to_turn)
                if success and degrees_to_turn != 0:
                        setValvePosition(valvename, target_degrees)
                        # Publish updated state to MQTT
                        try:
                                mqtt_client.publish('poolctl/stat/'+valvename+'/state',
                                                    target_degrees, qos=1, retain=True)
                        except Exception as e:
                                print("MQTT publish error for {}: {}".format(valvename, e))

                _decrement_pending(valvename)
                done_event.set()
                q.task_done()

def start_valve_threads():
        """Create and start one worker thread per valve."""
        import queue
        for vname in valvelist:
                q = queue.Queue()
                valve_queues[vname] = q
                t = threading.Thread(target=valve_thread_worker,
                                     args=(vname, q), daemon=True, name="valve-"+vname)
                t.start()
                valve_threads[vname] = t
        print("Started {} valve worker threads".format(len(valve_threads)))

def setValveList(valveChangeList, wait=True):
        """
        Submit move commands for one or more valves.
        Valves start moving in parallel immediately.
        If wait=True, blocks until all valves in this batch finish.
        Returns current valve positions dict.
        """
        global pending_count, pending_done

        # Filter to known valves only
        valveChangeList = {v: int(valveChangeList[v])
                           for v in valveChangeList if v in valvelist}
        if not valveChangeList:
                return getValveList()

        done_events = []
        with pending_lock:
                pending_count += len(valveChangeList)
                pending_done.clear()

        for valvename, target in valveChangeList.items():
                done_event = threading.Event()
                done_events.append(done_event)
                valve_queues[valvename].put((target, done_event))
                print("{}: queued target={}°".format(valvename, target))

        if wait:
                for ev in done_events:
                        ev.wait(timeout=120)

        return getValveList()


# ------------------------------------------------------------------
# Tuning helper -- moves a valve by time or degrees without updating
# the position table (used for calibration/tuning)
# ------------------------------------------------------------------
def turnValve(valvename, result, direction, degrees_to_turn=False, seconds_to_turn=False):
        if (direction < 0):
                RELAY=valvelist[valvename].get_CWrelay()
        elif (direction > 0):
                RELAY=valvelist[valvename].get_CCWrelay()
        else:
                result[valvename]='NoChange'
                return
        if degrees_to_turn:
                seconds_to_turn=degrees_to_turn * 0.210

        if DEBUG: print("Tuning: Activating RELAY "+str(RELAY)+" for "+str(seconds_to_turn)+" seconds")
        activateRELAY(RELAY, True)
        time.sleep(seconds_to_turn)
        activateRELAY(RELAY, False)
        result[valvename]='Success'


def equalSetting(setting1, setting2):
        if len(setting1) != len(setting2):
                print("ERROR: trying to compare settings of unequal length")
                return False
        for i in range(len(setting1)):
                if(setting1[i] != -1 and setting2[i] != -1 and setting1[i] != setting2[i]):
                        return False
        return True


def getFeatureList():
        valvesettings = getValveList()
        currentPos=tuple([valvesettings[column[i]] for i in range(len(column))])

        newFeatures = []
        for vpos in positionlist:
                if equalSetting(currentPos, vpos):
                        newFeatures=positionlist[vpos]
                        break

        # newFeatures contains the current features that are on
        fl={}
        for feature in featurelist:
                if feature in newFeatures:
                        fl[feature]="on"
                else:
                        fl[feature]="off"

        return fl

def setFeatureList(featureChangeList):
        if DEBUG: print("featureChangeList", featureChangeList)

        # Get the current list
        newFeatures=getFeatureList()
        print("newFeatures", newFeatures)
        # Update the current list with the requested changes
        for feature in featureChangeList:
                newFeatures[feature]=featureChangeList[feature]

        # Convert the set to a list of features that are on
        feat=[feat for feat in newFeatures if newFeatures[feat]=='on']

        # Search featureposition for the matching list to find the valve settings
        for ftuple in featureposition:
                if set(ftuple) == set(feat):
                        # Remove the don't cares
                        fp=featureposition[ftuple]
                        for f,d in list(fp.items()):
                                if d == -1: del fp[f]
                        try:
                                setValveList(fp)
                        except Exception as e:
                                print("setValveList exception: "+str(e))
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
                        if DEBUG: print("Activating RELAY "+str(poollist[p]))
                        activateRELAY(poollist[p], True)
                elif poolChangeList[p]=='off':
                        if p == "PoolLight": poolcolor='off'
                        if DEBUG: print("Deactivating RELAY "+str(poollist[p]))
                        activateRELAY(poollist[p], False)

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
                        # Variable speed pump -- read which speed relay is active
                        if DEBUG: print("Checking Pump Speed")
                        if   activateRELAY(poollist['PumpSpeed3'], read_set="read"):
                                poolsettings[p]='500'
                        elif activateRELAY(poollist['PumpSpeed2'], read_set="read"):
                                poolsettings[p]='1250'
                        elif activateRELAY(poollist['PumpSpeed1'], read_set="read"):
                                poolsettings[p]='2750'
                        elif activateRELAY(poollist['MainPump'],   read_set="read"):
                                poolsettings[p]='AUTO'
                        else:
                                poolsettings[p]='0'
                elif p == 'SpaHeater':
                        # Use the global variable instead of the relay setting
                        poolsettings[p]=SpaHeater
                elif activateRELAY(poollist[p], read_set="read"):
                        poolsettings[p]='on'
                else:
                        poolsettings[p]='off'

        return poolsettings

def cyclePoolLight(count):
        activateRELAY(poollist['PoolLight'], True)
        for i in range(count-1):
                activateRELAY(poollist['PoolLight'], False)
                time.sleep(0.25)
                activateRELAY(poollist['PoolLight'], True)
                time.sleep(0.25)

def poolLight(color):
        global poolcolor
        if color=="one":                                        cyclePoolLight(1)
        elif color=="white_green_blue_magenta"  or color=="SAM":      cyclePoolLight(2)
        elif color=="red_white_green_blue"      or color=="Party":    cyclePoolLight(3)
        elif color=="Romance":                                        cyclePoolLight(4)
        elif color=="blue_green"                or color=="Caribbean": cyclePoolLight(5)
        elif color=="red_white_blue"            or color=="American":  cyclePoolLight(6)
        elif color=="orange_red_magenta"        or color=="Cal_Sunset":cyclePoolLight(7)
        elif color=="magenta_blue_green_yellow" or color=="Royal":     cyclePoolLight(8)
        elif color=="Blue":    cyclePoolLight(9)
        elif color=="Green":   cyclePoolLight(10)
        elif color=="Red":     cyclePoolLight(11)
        elif color=="White":   cyclePoolLight(12)
        elif color=="Magenta": cyclePoolLight(13)
        elif color=="HOLD":    cyclePoolLight(14)
        elif color=="RECALL":  cyclePoolLight(15)
        poolcolor=color

def ValveAction(valveJSON):
        global SpaHeater
        try:
                result="None"
                settinglist={}
                print('valveJSON=', valveJSON)
                for settingType in valveJSON:
                        print('settingType=', settingType)
                        if settingType == "valveSetting":
                                valveChangeList=valveJSON["valveSetting"]
                                valveChangeList={v:valveChangeList[v] for v in valveChangeList if v in valvelist}
                                settinglist["valves"]=setValveList(valveChangeList)

                        elif settingType == "valveTuning":
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
                                        turnValve(valve, result, direction, seconds_to_turn=valveChange[valve])
                                else:
                                        print("Tuning "+valve+" by Turning in direction "+str(direction)+" for "+str(valveChange[valve])+" degrees")
                                        turnValve(valve, result, direction, degrees_to_turn=valveChange[valve])
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
                                print(poolChangeList)
                                if "SpaHeater" in poolChangeList:
                                        SpaHeater=poolChangeList["SpaHeater"]
                                print("SpaHeater = "+SpaHeater)
                                settinglist["pool"]=setPoolList(poolChangeList)

                        elif settingType == "SpaTempControl":
                                if SpaHeater == "on":
                                        if valveJSON["SpaTempControl"] == "on":
                                                poolChangeList={"SpaHeater":"on"}
                                        else:
                                                poolChangeList={"SpaHeater":"off"}
                                        settinglist["pool"]=setPoolList(poolChangeList)
                                else:
                                        print('Ignoring SpaTempControl because Spa Not On')

                        elif settingType == "poolColor":
                                poolLight(valveJSON["poolColor"]["Color"])
                                print("Main poolcolor="+poolcolor)
                                settinglist["pool"]=getPoolList()

                        result=json.dumps(settinglist)

        except Exception as e:
                result=json.dumps({"error": str(e)})
                print("ValveAction exception: ", e)

        return(result)


# ------------------------------------------------------------------
# MQTT broker connection settings
# ------------------------------------------------------------------
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


def on_connect(client, userdata, flags, rc):
        if rc:
                print("Error connecting to MQTT broker rc "+str(rc))
                return
        print("Connected to MQTT broker, result code "+str(rc))
        client.subscribe('poolctl/#')
        client.subscribe('alltemp/cmd/spaheater/set')
        client.subscribe('alltemp/sensor/poolspatemp/temperature')


def setup_mqtt_devices():
        # Publish availability FIRST so HA doesn't mark entities unavailable
        mqtt_client.publish('poolctl/availability', 'online', qos=1, retain=True)

        discovery_topic = 'homeassistant/select/PoolPump/config'
        payload = {
                "name":          'PoolPump',
                "command_topic": 'poolctl/cmd/PoolPump/set',
                "state_topic":   'poolctl/stat/PoolPump/state',
                "options":       ["Off", "500", "1250", "2750", "AUTO"],
                "unique_id":     'PoolPump',
                "device": {
                        "identifiers": ['PoolPump'],
                        "name":        'PoolPump',
                        "model":       "Pump",
                        "manufacturer":"poolctl"
                }
        }
        print(discovery_topic)
        mqtt_client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True)

        # Read the PoolPump HW settings to determine current pump speed at start.
        # There are 4 wires and ground going to the pump controller from the relay board.
        # One wire is power (MainPump) while the others set speed. Only one of the other three
        # should be active at any given time.  If none of the three is active then the pump
        # is running on its own internal program
        if   activateRELAY(poollist['PumpSpeed3'], read_set="read"):
                mqtt_client.publish('poolctl/stat/PoolPump/state', "500", qos=1, retain=True)
        elif activateRELAY(poollist['PumpSpeed2'], read_set="read"):
                mqtt_client.publish('poolctl/stat/PoolPump/state', "1250", qos=1, retain=True)
        elif activateRELAY(poollist['PumpSpeed1'], read_set="read"):
                mqtt_client.publish('poolctl/stat/PoolPump/state', "2750", qos=1, retain=True)
        elif activateRELAY(poollist['MainPump'],   read_set="read"):
                mqtt_client.publish('poolctl/stat/PoolPump/state', "AUTO", qos=1, retain=True)
        else:
                mqtt_client.publish('poolctl/stat/PoolPump/state', "Off", qos=1, retain=True)


        discovery_topic = 'homeassistant/select/PoolLight/config'
        payload = {
                "name":          'PoolLight',
                "command_topic": 'poolctl/cmd/PoolLight/set',
                "state_topic":   'poolctl/stat/PoolLight/state',
                "options":       ["Unknown","Blue","Green","Red","White","Magenta","Romance",
                                  "Blue_Green","Red_White_Blue","Orange_Red_Magenta",
                                  "Red_White_Green_Blue","White_Green_Blue_Magenta",
                                  "Magenta_Blue_Green_Yellow"],
                "unique_id":     'PoolLight',
                "device": {
                        "identifiers": ['PoolLight'],
                        "name":        'PoolLight',
                        "model":       "MultiColorLight",
                        "manufacturer":"poolctl"
                }
        }
        print(discovery_topic)
        mqtt_client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True)

        discovery_topic = 'homeassistant/switch/SpaHeaterMasterSwitch/config'
        payload = {
                "name":           'SpaHeater Switch',
                "command_topic":  'poolctl/cmd/SpaHeater/set',
                "state_topic":    'poolctl/stat/SpaHeater/state',
                "payload_on":     "on",
                "payload_off":    "off",
                "state_on":       "on",
                "state_off":      "off",
                "unique_id":      'SpaHeaterSwitch',
                "availability_topic": "poolctl/availability",
                "device": {
                        "identifiers": ['SpaHeater Switch'],
                        "name":        'Spa Heater Master Switch',
                        "model":       "Custom",
                        "manufacturer":"poolctl"
                }
        }
        print(discovery_topic)
        mqtt_client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True)

        # Actual relay state (read-only, driven by poolctl)
        discovery_topic = 'homeassistant/binary_sensor/SpaHeaterRelay/config'
        payload = {
                "name":               "Spa Heater Relay",
                "unique_id":          "spa_heater_relay",
                "state_topic":        "poolctl/stat/SpaHeaterRelay/state",
                "payload_on":         "on",
                "payload_off":        "off",
                "availability_topic": "poolctl/availability",
                "icon":               "mdi:fire",
                "device": {
                        "identifiers":  ["spa_heater_relay"],
                        "name":         "Spa Heater Relay Status",
                        "manufacturer": "poolctl"
                }
        }
        print(discovery_topic)
        mqtt_client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True)

        # Publish initial relay state immediately after discovery
        initial_relay_state = 'on' if SpaHeater == 'on' else 'off'
        mqtt_client.publish('poolctl/stat/SpaHeaterRelay/state', initial_relay_state, qos=1, retain=True)
        mqtt_client.publish('poolctl/stat/SpaHeater/state', SpaHeater, qos=1, retain=True)

        valvesettings=getValveList()
        print("valvelist:\n"+json.dumps(valvesettings, indent=4))

        for valve in valvesettings:
                discovery_topic = 'homeassistant/number/'+valve+'/config'
                payload = {
                        "name":                valve+' Direction',
                        "command_topic":       'poolctl/cmd/'+valve+'/set',
                        "state_topic":         'poolctl/stat/'+valve+'/state',
                        "min":                 0,
                        "max":                 360,
                        "step":                1,
                        "unit_of_measurement": "°",
                        "unique_id":           valve.lower()+'_direction',
                        "availability_topic":  'poolctl/valve/'+valve+'/availability',
                        "retain":              True,
                        "device": {
                                "identifiers": ['PoolValve_'+valve],
                                "name":        valve+' Direction',
                                "model":       "Custom",
                                "manufacturer":"poolctl"
                        }
                }
                mqtt_client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True)
                mqtt_client.publish('poolctl/valve/'+valve+'/availability', 'online', qos=1, retain=True)
                mqtt_client.publish('poolctl/stat/' +valve+'/state', valvesettings[valve], qos=1, retain=True)

                # Sensor discovery for dashboard display (read-only position)
                discovery_topic = 'homeassistant/sensor/'+valve+'/config'
                payload = {
                        "name":                valve+' Position',
                        "state_topic":         'poolctl/stat/'+valve+'/state',
                        "unit_of_measurement": "°",
                        "unique_id":           valve.lower()+'_position',
                        "availability_topic":  'poolctl/valve/'+valve+'/availability',
                        "icon":                "mdi:rotate-right",
                        "device": {
                                "identifiers": ['PoolValve_'+valve],
                                "name":        valve+' Direction',
                                "model":       "Custom",
                                "manufacturer":"poolctl"
                        }
                }
                mqtt_client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True)


def on_message(client, userdata, message):
        command = str(message.payload.decode('utf-8'))
        topic   = message.topic.split('/')
        print("[{}] MQTT Topic: {} = {}".format(datetime.datetime.now(), topic, command))

        # Inter-daemon: alltemp telling us to turn the relay on/off
        if message.topic == 'alltemp/cmd/spaheater/set':
                t = threading.Thread(target=handle_spaheater_relay, args=(client, command), daemon=True)
                t.start()
                return
        elif message.topic == 'alltemp/sensor/poolspatemp/temperature':
                try:
                        data = json.loads(command)
                        print("alltemp reports temperature of ", data['temperature'])
                except Exception as e:
                        print("Error parsing temperature: ", e)
                return

        if topic[0] != 'poolctl' or len(topic) < 4:
                print("ERROR: topic too short or wrong prefix: "+message.topic)
                return

        t = threading.Thread(target=handle_message, args=(client, topic, command), daemon=True)
        t.start()


def handle_spaheater_relay(client, command):
        global SpaHeater
        if SpaHeater == 'on':
                print("alltemp requested heater relay: ", command)
                valveJSON = {"SpaTempControl": command}
                ValveAction(valveJSON)
                client.publish('poolctl/stat/SpaHeaterRelay/state', command.lower(), qos=1, retain=True)
        else:
                print("Ignoring alltemp heater request '"+command+"' — master switch is off")


def handle_message(client, topic, command):
        try:
                if topic[1] == 'cmd' and topic[3] == 'set':
                        if topic[2] == 'PoolPump':
                                if   command == 'Off':   valveJSON={"poolSetting":{"MainPump":"off","PumpSpeed1":"off","PumpSpeed2":"off","PumpSpeed3":"off"}}
                                elif command == '2750':  valveJSON={"poolSetting":{"MainPump":"on","PumpSpeed1":"on","PumpSpeed2":"off","PumpSpeed3":"off"}}
                                elif command == '1250':  valveJSON={"poolSetting":{"MainPump":"on","PumpSpeed2":"on","PumpSpeed1":"off","PumpSpeed3":"off"}}
                                elif command == '500':   valveJSON={"poolSetting":{"MainPump":"on","PumpSpeed3":"on","PumpSpeed1":"off","PumpSpeed2":"off"}}
                                elif command == 'AUTO':  valveJSON={"poolSetting":{"MainPump":"on","PumpSpeed3":"off","PumpSpeed1":"off","PumpSpeed2":"off"}}
                                else:
                                        print("Unknown PoolPump command: "+command)
                                        return
                        elif topic[2] == 'PoolLight':
                                if command == 'Off': valveJSON={"poolSetting":{"PoolLight":"off"}}
                                else:                valveJSON={"poolColor":{"Color": command}}
                        elif topic[2] == 'SpaHeater':
                                print("Turning SpaHeater master switch ", command)
                                valveJSON={"poolSetting": {"SpaHeater": command}}
                                if command == 'off':
                                        # Safety: kill the relay immediately when master switch turns off
                                        ValveAction({"SpaTempControl": "off"})
                                        client.publish('poolctl/stat/SpaHeaterRelay/state', 'off', qos=1, retain=True)
                        else:
                                valveJSON={"valveSetting": {topic[2]: int(command)}}

                        print("valveJSON from MQTT = " + json.dumps(valveJSON))
                        result = ValveAction(valveJSON)
                        client.publish('poolctl/stat/'+topic[2]+'/state', command, qos=1, retain=True)

                elif topic[1] == 'cmd' and topic[2] == 'valveSettings' and topic[3] == 'get':
                        valvesettings = getValveList()
                        for valve in valvesettings:
                                client.publish('poolctl/stat/'+valve+'/state', valvesettings[valve], qos=1, retain=True)
                        client.publish('poolctl/stat/valveSettings/state', json.dumps(valvesettings), qos=1, retain=True)

                elif topic[1] == 'cmd' and topic[2] == 'poolSettings' and topic[3] == 'get':
                        poolsettings = getPoolList()
                        # If we restarted and don't know the pool light color, set to unknown
                        if poolsettings['PoolLight'] == "RECALL": poolsettings['PoolLight'] = "Unknown"
                        client.publish('poolctl/stat/poolSettings/state', json.dumps(poolsettings), qos=1, retain=True)
                        client.publish('poolctl/stat/PoolPump/state',    poolsettings['MainPump'],  qos=1, retain=True)
                        client.publish('poolctl/stat/PoolLight/state',   poolsettings['PoolLight'], qos=1, retain=True)
                        client.publish('poolctl/stat/SpaHeater/state',   poolsettings['SpaHeater'], qos=1, retain=True)

                elif topic[1] == 'stat' and topic[3] == 'state':
                        print("Skipping State Update")

        except Exception as e:
                print("handle_message exception: ", e)


def mqtt_listener():
        global mqtt_client
        mqtt_client = mqtt.Client()
        mqtt_client.on_message = on_message
        mqtt_client.on_connect = on_connect

        print("Connecting to broker: "+broker+":"+str(port))
        mqtt_client.connect(broker, port, keepalive=120)

        setup_mqtt_devices()
        mqtt_client.loop_forever()


def tcp_listener():
        sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address=('0.0.0.0', 2222)
        sock.bind(server_address)
        sock.listen(1)

        while True:
                # Wait for a connection
                connection, client_address=sock.accept()
                if (client_address[0] != '172.16.2.254' and client_address[0] != 'localhost' and client_address[0] != '127.0.0.1'):
                        print("connection from unknown IP "+client_address[0])
                        connection.close()
                        continue

                try:
                        valvechanges=b""
                        while True:
                                data = connection.recv(16)
                                if data: valvechanges+=data
                                else:    break
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

                print(result)
                connection.sendall((result+'\n').encode('utf-8'))
                connection.close()


# Only start the valve server if we are called standalone
if not 'poolctl' in sys.modules:
        if activateRELAY(poollist['SpaHeater'], read_set="read"):
                SpaHeater='on'
        else:
                SpaHeater='off'

        # Load valve positions from file into memory
        loadValvePositions()

        # Set the poolcolor to a RECALL on start
        poolLight('RECALL')

        # Start one dedicated worker thread per valve
        start_valve_threads()

        # Create a thread for the TCP listener
        tcp_thread = threading.Thread(target=tcp_listener, daemon=True)
        tcp_thread.start()

        # Create a thread for the MQTT listener
        mqtt_thread = threading.Thread(target=mqtt_listener, daemon=True)
        mqtt_thread.start()

        # Keep main thread alive; write valve positions to disk on exit
        try:
                while True:
                        time.sleep(1)
        except KeyboardInterrupt:
                print("Shutting down...")
                writeValveSettings()
                # Signal all valve worker threads to stop
                for vname, q in valve_queues.items():
                        q.put(None)
                GPIO.cleanup()

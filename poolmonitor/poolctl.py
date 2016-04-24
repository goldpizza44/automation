#!/usr/bin/python -u

import RPi.GPIO as GPIO
import time
import socket
import sys
import threading
import json

global DEBUG
DEBUG=1

# Set the GPIO pins to be used for the binary selectors
A0=7  #A0=26
A1=8  #A1=24
A2=25 #A2=22
A3=24 #A3=18
A4=23 #A4=16
A5=18 #A5=12
A6=15 #A6=10
A7=14 #A7=8
A12=3 #A12=5
A13=2 #A13=3
A14=27 #A14=13

# P5 Header
A8=28
A9=29
A10=30
A11=31

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




def activateRELAY(relay,setting="False",read_set="set"):

	# These are negative logic.
	if(relay==0): RELAY=A0;	setting=not setting
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

	if (read_set == "set"):
		return GPIO.output(RELAY,setting)
	else:
		return GPIO.input(RELAY)

# CONFIG columns
VALVENUM=0
VALVENAME=1
VALVE_CW=2
VALVE_CCW=3


class valve():
	def __init__(self,num,name,cw_relay,ccw_relay):
		self.num=num
		self.name=name
		self.cw_relay=int(cw_relay)
		self.ccw_relay=int(ccw_relay)

	def get_CWrelay(self):	return self.cw_relay

	def get_CCWrelay(self): return self.ccw_relay
 

global valvelist
valvelist={}
f=open("/var/www/html/config/valve_config","r")
for l in f:
	if ("#" in l):
		continue
	data=l.split()
	data=[ d.decode('UTF-8') for d in data ]
	if(len(data)>=4):
		valvelist[data[VALVENAME]]=valve(data[VALVENUM],data[VALVENAME],data[VALVE_CW],data[VALVE_CCW])

f.close()

global positionlist
global featurelist
global featureposition
positionlist={}
featurelist={}
featureposition={}
column=[]

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
			column.append(data[i].decode('UTF-8'))

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
		flist=[ feature.decode('UTF-8') for feature in flist ]
                positionlist[vpos]=flist
		featureposition[tuple(flist)]=vpos1

		for feature in flist:
			if feature in featurelist: featurelist[feature].append(vpos)
			else:
		                featurelist[feature] = [ vpos ]
		
f.close()

# These are the number of seconds that a valve will turn to get to a specific
# position.  The first number is the degrees and second is seconds
SECS={	45:9.5, 90:19, 135:28.5, 180:40,  }

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
		if DEBUG: print "Activating RELAY "+str(RELAY)+" for "+str(SECS[degrees_to_turn])+" seconds"
		activateRELAY(RELAY,True)
		time.sleep(SECS[degrees_to_turn])
		if DEBUG: print "Deactivating RELAY "+str(RELAY)
		activateRELAY(RELAY,False)
		result[valvename]='Success'
	elif degrees_to_turn==1:
		print "RELAY: "+str(RELAY)+" Don't care value of -1...skipping"
	else:
		result[valvename]='InvalidDegrees '+str(degrees_to_turn)
		print "Invalid Degrees "+str(degrees_to_turn)+" ... No change made"

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

	if DEBUG: print "valveChangeList",valveChangeList
	for valve in valveChangeList:
		if(not(valve in valveThread)):
			degrees_to_turn=valveChangeList[valve]-valvesettings[valve]
			valveResult[valve]='Unknown'
			try:
				valveThread[valve]=threading.Thread(target=setValve, args=(valve,degrees_to_turn,valveResult,))
				valveThread[valve].start()
			except:
				print "Error:  unable to start Thread for valve "+valve
		else:
			print "Can't change Valve "+valve+" to two different settings at the same time"

	# The valves should be turning now...Wait for them to finish.
	# Join each thread for a minimum of 45 secs
	for v in valveThread:
		valveThread[v].join(45)

	for v in valveResult:
		if(valveResult[v]=='Unknown'):
			# For some reason the thread did not finish in 40 seconds
			# try to kill the thread
			print "Thread for "+v+" had Result Unknown"
		if(valveResult[v]=='Success'):	valvesettings[v]=valveChangeList[v]

	# For the valve changes that were successful, write them back to the file
	f=open("/var/www/html/config/valve_settings","w")
	for v in valvesettings:	f.write(v+'	'+str(valvesettings[v])+'\n')
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

	if DEBUG: print "featureChangeList",featureChangeList

	# Get the current list
	newFeatures=getFeatureList()
	print "newFeatures",newFeatures
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
			for f,d in fp.items():
				if d == -1: del fp[f]
			try:
				setValveList(fp )
			except Exception,e:
	                        print "setValveList exception: "+str(e)

			break

	return newFeatures

poollist={'PoolLight':12,'MainPump':13,'SpaHeater':14}
poolcolor='off'

def setPoolList(poolChangeList):
	global poolcolor
	for p in poolChangeList:
		if poolChangeList[p]=='on':
			if DEBUG: print "Activating RELAY "+str(poollist[p])
			activateRELAY(poollist[p],True)
		elif poolChangeList[p]=='off':
			if p == "PoolLight":
				poolcolor='off'
			if DEBUG: print "Deactivating RELAY "+str(poollist[p])
			activateRELAY(poollist[p],False)

	return getPoolList()


def getPoolList():
	poolsettings={}
	for p in poollist:
		if p == 'PoolLight':
			poolsettings[p]=poolcolor
		elif p == 'MainPump':
			# Variable speed pump read speed...for now 
			# Hard code in speed
			if activateRELAY(poollist[p],read_set="read"):
				poolsettings[p]='3450'
			else:
				poolsettings[p]='0'
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

def startValveServer():
	sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	server_address=('0.0.0.0',2222)
	sock.bind(server_address)

	sock.listen(1)

	while True:
		# Wait for a connection
		connection, client_address=sock.accept()
		if (client_address[0] != '172.16.2.254' and client_address[0] != 'localhost'):
			print "connection from unknown IP "+client_address[0]
			connection.close()
			continue

		try:
			# Receive the data in small chunks and retransmit it
			valvechanges=""
			while True:
				data = connection.recv(16)

				if data:	valvechanges+=data
				else:		break

			try:
				valveJSON=json.loads(valvechanges)
			except Exception,e:
				result='{"Invalid JSON":"all"}'
				continue

			try:
				result="None"
				settinglist={}
				print valveJSON
				for settingType in valveJSON:
					if settingType == "valveSetting":
						# Remove valves that have invalid names
						valveChangeList=valveJSON["valveSetting"]
						valveChangeList={v:valveChangeList[v] for v in valveChangeList if v in valvelist}
						settinglist["valves"]=setValveList(valveChangeList)
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
						settinglist["pool"]=setPoolList(poolChangeList)
					elif settingType == "poolColor":
						poolLight(valveJSON["poolColor"]["Color"])
						print "Main poolcolor="+poolcolor
						settinglist["pool"]=getPoolList()

					result=json.dumps(settinglist)

			except Exception,e: 
				result='{"Exception":"'+str(e)+'"}'

				print "Exception: "+str(e)

		finally:
			print result
			connection.sendall(result+'\n')

			# Clean up the connection
			connection.close()


# Only start the valve server if we are called standalone
if not 'poolctl' in sys.modules: startValveServer()

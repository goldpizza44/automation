#!/usr/bin/python -u
from w1thermsensor import W1ThermSensor
import wiringpi2 as wpi
import time
import socket
import json
import threading
import os
import collections

OUTCSV="/var/www/html/tempdata.csv"
DEBUG=1


DS18B20=W1ThermSensor()

# This is an unordered dictionary...
#sensor_name = {
#"041637c1bcff":"AlexanderBedroom",
#"041637f543ff":"GuestBedroom",
#"041637bd5bff":"NikitaBedroom",
#"041637ffddff":"DanielBedroom",
#"0416380260ff":"UpstairsHall",
#"80000027968e":"KitchenDiningRoomTheatre",
#"800000046e8c":"GreatRoomOffice",
#}

# Using an OrderedDict so that the columns will print in order
sensor_name = collections.OrderedDict()
sensor_name["041637c1bcff"]="AlexanderBedroom"
sensor_name["041637f543ff"]="GuestBedroom"
sensor_name["041637bd5bff"]="NikitaBedroom"
sensor_name["041637ffddff"]="DanielBedroom"
sensor_name["0416380260ff"]="UpstairsHall"
sensor_name["80000027968e"]="KitchenDiningRoomTheatre"
sensor_name["800000046e8c"]="GreatRoomOffice"

thermostat = { "UpstairsHall", "KitchenDiningRoomTheatre", "GreatRoomOffice", "MasterBedroom" }

sensor_avg = {}
sensor_current = {}
temp_target = {}

wpi.wiringPiSetup()
CALL_HEAT_COOL_PIN=1
HEAT_COOL_PIN=2
FAN_PIN=3

thermostat_pinlist={}
thermostat_pinlist[("GreatRoomOffice",CALL_HEAT_COOL_PIN)]=21 # brown/white
thermostat_pinlist[("GreatRoomOffice",HEAT_COOL_PIN)]=22      # orange/white
thermostat_pinlist[("GreatRoomOffice",FAN_PIN)]=23            # green/white

thermostat_pinlist[("UpstairsHall",CALL_HEAT_COOL_PIN)]=12    # brown/white
thermostat_pinlist[("UpstairsHall",HEAT_COOL_PIN)]=13         # orange/white
thermostat_pinlist[("UpstairsHall",FAN_PIN)]=14               # green/white

thermostat_pinlist[("KitchenDiningRoomTheatre",CALL_HEAT_COOL_PIN)]=6 # brown/white
thermostat_pinlist[("KitchenDiningRoomTheatre",HEAT_COOL_PIN)]=10     # orange/white
thermostat_pinlist[("KitchenDiningRoomTheatre",FAN_PIN)]=11           # green/white

thermostat_pinlist[("MasterBedroom",CALL_HEAT_COOL_PIN)]=0 # brown/white
thermostat_pinlist[("MasterBedroom",HEAT_COOL_PIN)]=2      # orange/white
thermostat_pinlist[("MasterBedroom",FAN_PIN)]=3            # green/white

# GPIO/RELAYS have negative logic.  zero switches on the relay
# for use with HEAT_COOL_PIN
COOL_SELECT=1  # COOL is NormallyClosed
HEAT_SELECT=0  # HEAT is NormallyOpen

HVAC_ON=0
HVAC_OFF=1

# Set the pins to OUTPUTs
for pin in thermostat:
	wpi.pinMode(thermostat_pinlist[(pin,CALL_HEAT_COOL_PIN)],1)
	wpi.pinMode(thermostat_pinlist[(pin,HEAT_COOL_PIN)],1)
	wpi.pinMode(thermostat_pinlist[(pin,FAN_PIN)],1)

HEADER="TIME,COUNT"
for sensorID,sensorName in sensor_name.iteritems():
	HEADER=HEADER+","+sensorName
	sensor_current[sensorName]=0

for unit in thermostat:
	temp_target[unit]=0

HEADER=HEADER+"\n"
print "HEADER="+HEADER

# Open the CSV datafile as global 'f'
try:
	if os.stat(OUTCSV).st_size > 0:
		f=open(OUTCSV,"a")
	else:
		f=open(OUTCSV,"a")
		f.write(HEADER)
except:
	f=open(OUTCSV,"a")
	f.write("0"+HEADER)


def clearSensorAVG():
	for sensorID,sensorName in sensor_name.iteritems():
		if DEBUG == 1:  print "Clearing "+sensorName
		sensor_avg[sensorName]=0

def monitorTemps():
	global sensor_current
	clearSensorAVG()
	lastminute=int(time.strftime("%M"))
	r = 0
	count=0.0
	while True:

		r += 1
		count += 1.0

		# Read the DS18B20s
		for sensor in W1ThermSensor.get_available_sensors():
			temp=sensor.get_temperature(W1ThermSensor.DEGREES_F)

			# If the sensor is reading super high then something is wrong..try to read again
			while ( temp > 120 ):
				print("Sensor %s has high temp %.2f" % (sensor_name[sensor.id], temp))
				time.sleep(0.2)
				temp=sensor.get_temperature(W1ThermSensor.DEGREES_F)


			if (DEBUG == 1):
				print("Sensor %s has temperature %.2f" % (sensor_name[sensor.id], temp))
			sensor_avg[sensor_name[sensor.id]]+= temp
			time.sleep(0.2)

		if (DEBUG == 1):
			print("-")

		minute=int(time.strftime("%M"))

		if (minute != lastminute):
			# Minute just changed.  Write a line to the CSV file
			f.write("{},{}".format(time.strftime("%Y/%m/%d %H:%M:%S"),r))

			for sensorID,sensorName in sensor_name.iteritems():
				f.write(",{:3.2f}".format(sensor_avg[sensorName]/count))
				sensor_current[sensorName]=sensor_avg[sensorName]/count
				print "Setting sensor_current["+sensorName+"]="+str(sensor_current[sensorName])


			f.write("\n")

			f.flush()

			clearSensorAVG()

			count=0
			lastminute=minute




		time.sleep(3) # Overall INTERVAL second polling.

def listenForInstruction():
	global sensor_current
	# Listen for instructions on TCP port 2222
	sock=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	server_address=('0.0.0.0',2222)
	sock.bind(server_address)
	sock.listen(1)

	while True:
		# Wait for a connection
		connection, client_address=sock.accept()
		if (client_address[0] != '172.16.2.254' and client_address[0] != '127.0.0.1'):
			print "connection from unknown IP "+client_address[0]
			connection.close()
			continue
		try:
			# Receive the data in small chunks and retransmit it
			instruction=""
			while True:
				data=connection.recv(16)

				if data:	instruction+=data
				else:		break

			try:
				instructionJSON=json.loads(instruction)
			
			except Exception,e:
				result='{"Invalid JSON":"all"}'
				continue

			try:
				result="None"
				instructionlist={}
				print instructionJSON

				for inst in instructionJSON:
					if inst == "getTemp":
						if instructionJSON[inst] in sensor_name.values():
							result='{"'+instructionJSON[inst]+'":'+str(sensor_current[instructionJSON[inst]])+'}'
						else:
							result='{"getTemp":"no"}'

					elif inst == "setTemp":
						if instructionJSON[inst] in thermostat:
							temp_target[instructionJSON[inst]]=1
							result='{"setTemp":"yes"}'
						else:
							result='{"setTemp":"no"}'
					else:
						result='{"UnknownInstruction":"'+inst+'"}'

			except Exception,e:
				result='{"Exception":"'+str(e)+'"}'
				print "Exception: "+str(e)

		finally:
			print result
			connection.sendall(result+'\n')

			# Clean up the connection
			connection.close()



monitorThread=threading.Thread(target=monitorTemps)
monitorThread.start()

instructionThread=threading.Thread(target=listenForInstruction)
instructionThread.start()

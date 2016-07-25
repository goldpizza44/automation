#!/usr/bin/python -u
from w1thermsensor import W1ThermSensor
import wiringpi2 as wpi
import time
import socket
import json
import threading
import os

OUTCSV="/var/www/html/tempdata.csv"
DEBUG=1


DS18B20=W1ThermSensor()

sensor_name = {
"041637c1bcff":"AlexanderBedroom",
"041637f543ff":"GuestBedroom",
"041637bd5bff":"NikitaBedroom",
"041637ffddff":"DanielBedroom",
"0416380260ff":"UpstairsHall",
"80000027968e":"KitchenDiningRoomTheatre",
"800000046e8c":"GreatRoomOffice",
}
sensor_avg = {
"AlexanderBedroom":0,
"GuestBedroom":0,
"NikitaBedroom":0,
"DanielBedroom":0,
"UpstairsHall":0,
"KitchenDiningRoomTheatre":0,
"GreatRoomOffice":0
}


wpi.wiringPiSetup()
CALL_HEAT_COOL_PIN=21
HEAT_COOL_PIN=22
FAN_PIN=23

# GPIO/RELAYS have negative logic.  zero switches on the relay
# for use with HEAT_COOL_PIN
COOL_SELECT=1  # COOL is NormallyClosed
HEAT_SELECT=0  # HEAT is NormallyOpen

HVAC_ON=0
HVAC_OFF=1

# Set the pins to OUTPUTs
wpi.pinMode(CALL_HEAT_COOL_PIN,1)
wpi.pinMode(HEAT_COOL_PIN,1)
wpi.pinMode(FAN_PIN,1)

HEADER="TIME,COUNT,AlexanderBedroom,GuestBedroom,NikitaBedroom,DanielBedroom,UpstairsHall,KitchenDiningRoomTheatre,GreatRoomOffice\n"

try:
	if os.stat(OUTCSV).st_size > 0:
		f=open(OUTCSV,"a")
	else:
		f=open(OUTCSV,"a")
		f.write(HEADER)
except:
	f=open(OUTCSV,"a")
	f.write("0"+HEADER)


def monitorTemps():
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
			f.write("{},{},{:3.2f},{:3.2f},{:3.2f},{:3.2f},{:3.2f},{:3.2f},{:3.2f}\n".format(
				time.strftime("%Y/%m/%d %H:%M:%S"),r, 
				sensor_avg["AlexanderBedroom"]/count,
				sensor_avg["GuestBedroom"]/count,
				sensor_avg["NikitaBedroom"]/count,
				sensor_avg["DanielBedroom"]/count,
				sensor_avg["UpstairsHall"]/count,
				sensor_avg["KitchenDiningRoomTheatre"]/count,
				sensor_avg["GreatRoomOffice"]/count))

			f.flush()

			sensor_avg["AlexanderBedroom"]=0
			sensor_avg["GuestBedroom"]=0
			sensor_avg["NikitaBedroom"]=0
			sensor_avg["DanielBedroom"]=0
			sensor_avg["UpstairsHall"]=0
			sensor_avg["KitchenDiningRoomTheatre"]=0
			sensor_avg["GreatRoomOffice"]=0

			count=0
			lastminute=minute




		time.sleep(3) # Overall INTERVAL second polling.

def listenForInstruction():
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
						result='{"Temperature":"yes"}'
					elif inst == "setTemp":
						result='{"SetTemp":"yes"}'
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

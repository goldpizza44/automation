#!/usr/bin/python -u
from w1thermsensor import W1ThermSensor
import time
#import RPi.GPIO as GPIO
import os

OUTCSV="/var/www/html/tempdata.csv"
DEBUG=1


DS18B20=W1ThermSensor()

sensor_name = {
"041637c1bcff":"AlexanderBedroom",
"041637f543ff":"GuestBedroom",
"041637bd5bff":"NikitaBedroom",
"041637ffddff":"DanielBedroom",  # Daniel Bedroom
"0416380260ff":"UpstairsHall"
}
sensor_avg = {
"AlexanderBedroom":0,
"GuestBedroom":0,
"NikitaBedroom":0,
"DanielBedroom":0,
"UpstairsHall":0
}

r = 0
count=0.0

#GPIO.setmode(GPIO.BOARD)
#GPIO.setwarnings(False)

HEADER="TIME,COUNT,AlexanderBedroom,GuestBedroom,NikitaBedroom,DanielBedroom,UpstairsHall\n"

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

	r += 1
	count += 1.0

	# Read the DS18B20s
	for sensor in W1ThermSensor.get_available_sensors():
		temp=sensor.get_temperature(W1ThermSensor.DEGREES_F)

		# If the sensor is reading super high then something is wrong..try to read again
		while ( temp > 120 ):
			time.sleep(0.2)
			temp=sensor.get_temperature(W1ThermSensor.DEGREES_F)


		print("Sensor %s has temperature %.2f" % (sensor_name[sensor.id], temp))
		sensor_avg[sensor_name[sensor.id]]+= temp
		time.sleep(0.2)
	print("-")
	minute=int(time.strftime("%M"))

	if (minute != lastminute):
		f.write("{},{},{:3.2f},{:3.2f},{:3.2f},{:3.2f},{:3.2f}\n".format(
        		time.strftime("%Y/%m/%d %H:%M:%S"),r, 
			sensor_avg["AlexanderBedroom"]/count,
			sensor_avg["GuestBedroom"]/count,
			sensor_avg["NikitaBedroom"]/count,
			sensor_avg["DanielBedroom"]/count,
			sensor_avg["UpstairsHall"]/count))

		f.flush()

		sensor_avg["AlexanderBedroom"]=0
		sensor_avg["GuestBedroom"]=0
		sensor_avg["NikitaBedroom"]=0
		sensor_avg["DanielBedroom"]=0
		sensor_avg["UpstairsHall"]=0

		count=0
		lastminute=minute




	time.sleep(3) # Overall INTERVAL second polling.





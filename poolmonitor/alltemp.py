#!/usr/bin/python -u
from w1thermsensor import W1ThermSensor
import time
import pigpio
import DHT22
import RPi.GPIO as GPIO
from math import log10
import os

# Constants to calculate temp from thermistor
# These three items together will shift the line up and down
THERMISTORNOMINAL=10000.0   
TEMPERATURENOMINAL=25.0   
SERIESRESISTOR=9500.0

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


pi = pigpio.pi()

#   s = DHT22.sensor(pi, 22, LED=16, power=8)
DHT22sensor = DHT22.sensor(pi, 17)

DS18B20=W1ThermSensor()

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

	DHT22sensor.trigger()
	time.sleep(0.2)

	# Read the DS18B20
	DS18B20_temp = DS18B20.get_temperature(W1ThermSensor.DEGREES_F)

	# Read the Thermistor
	ThermistorRAW=readadc(TempADC,SPICLK,SPIMOSI,SPIMISO,SPICS)

	ADvalue=1.0/((1023.0/ThermistorRAW)-1)
	resistance_ratio=(SERIESRESISTOR / THERMISTORNOMINAL) * ADvalue

	steinhart=log10(resistance_ratio)/BCOEFFICIENT
	steinhart=steinhart + (1.0/(TEMPERATURENOMINAL+273.15))
	TempKelvins = 1.0/steinhart
	ThermistorTemp_F=(TempKelvins-273.20)*9.0/5.0 +32

	# Read the Pressure Sensor
	PressureRAW=readadc(PressureADC,SPICLK,SPIMOSI,SPIMISO,SPICS)
	# 126 raw value=0 PSI   320 raw value = 13PSI   500 raw value = 25PSI
	FilterPressure=(PressureRAW * 0.066854)-8.42246

	DHT22_temp=(DHT22sensor.temperature()*(9.0/5.0))+32.0
	DHT22_humidity=DHT22sensor.humidity()

	DS18B20_temp_avg     += DS18B20_temp
	ThermistorTemp_F_avg += ThermistorTemp_F
	DHT22_temp_avg       += DHT22_temp
	DHT22_humidity_avg   += DHT22_humidity
	ThermistorRAW_avg    += ThermistorRAW
	PressureRAW_avg      += PressureRAW

	if (DEBUG==1):
		print "{},{},{},{},{},{:3.2f},{},{},{}".format(
			time.strftime("%Y/%m/%d %H:%M:%S"),r,
			DHT22_humidity,DHT22_temp,
			DS18B20_temp,ThermistorTemp_F,ThermistorRAW,PressureRAW,FilterPressure)

	minute=int(time.strftime("%M"))

	if (minute != lastminute):
		f.write("{},{},{:3.2f},{:3.2f},{:3.2f},{:3.2f},{:5.2f},{:5.2f},{:3.2f}\n".format(
        		time.strftime("%Y/%m/%d %H:%M:%S"),r, 
			DHT22_humidity_avg/count, DHT22_temp_avg/count, 
			DS18B20_temp_avg/count, ThermistorTemp_F_avg/count, ThermistorRAW_avg/count,
			PressureRAW_avg/count,((PressureRAW_avg/count)*0.066854)-8.42246))

		f.flush()

		DS18B20_temp_avg=0
		ThermistorTemp_F_avg=0
		DHT22_temp_avg=0
		DHT22_humidity_avg=0
		ThermistorRAW_avg=0
		PressureRAW_avg=0

		count=0
		lastminute=minute




	time.sleep(3) # Overall INTERVAL second polling.

DHT22sensor.cancel()

pi.stop()




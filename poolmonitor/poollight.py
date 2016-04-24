#!/usr/bin/python

import RPi.GPIO as GPIO
import time
import sys,getopt

# Set the GPIO pins to be used for the binary selectors
A0=40
A1=36
A2=32



GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(A2, GPIO.OUT)
GPIO.setup(A1, GPIO.OUT)
GPIO.setup(A0, GPIO.OUT)

def activateSENSOR(sensor):
	if(sensor==0):
		GPIO.output(A2,False)
		GPIO.output(A1,False)
		GPIO.output(A0,False)
	if(sensor==1):
		GPIO.output(A2,False) 
		GPIO.output(A1,False)
		GPIO.output(A0,True)
	if(sensor==2):
		GPIO.output(A2,False) 
		GPIO.output(A1,True)
		GPIO.output(A0,False)
	if(sensor==3):
		GPIO.output(A2,False) 
		GPIO.output(A1,True)
		GPIO.output(A0,True)
	if(sensor==4):
		GPIO.output(A2,True) 
		GPIO.output(A1,False)
		GPIO.output(A0,False)
	if(sensor==5):
		GPIO.output(A2,True) 
		GPIO.output(A1,False)
		GPIO.output(A0,True)
	if(sensor==6):
		GPIO.output(A2,True) 
		GPIO.output(A1,True)
		GPIO.output(A0,False)
	if(sensor==7):
		GPIO.output(A2,True)
		GPIO.output(A1,True)
		GPIO.output(A0,True)

def Blink(sensorTimes,speed):
	for i in range(0,sensorTimes):
		for j in range(0,8):
			activateSENSOR(j)
			time.sleep(speed)

def main(argv):
	try:
		opts,args=getopt.getopt(argv,"i:s:",["iterations=","speed="])

	except getopt.GetoptError:
		print("cycle.py -i iterations -s speed")
		sys.exit(2)

	iterations=0
	speed=0.0

	for opt, arg in opts:
		if opt == '-i':
			iterations=int(arg)
		elif opt == '-s':
			speed=float(arg)
		else:
			print("cycle.py -i iterations -s speed")
			sys.exit(3)


	if(iterations==0):
		iterations = int(raw_input("Enter total sensorber of times to blink: "))

	if (speed==0.0):
		speed = float(raw_input("Enter length of each blink(seconds): "))

	print ("iterations: "+str(iterations))
	print ("speed: "+str(speed))

	Blink(iterations,speed)


if __name__ == "__main__":
	main(sys.argv[1:])

#!/usr/bin/python

import RPi.GPIO as GPIO
import time
import sys,getopt

# Set the GPIO pins to be used for the binary selectors
A0=26
A1=24
A2=22
A3=18
A4=16
A5=12
A6=10
A7=8




GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(A0, GPIO.OUT)
GPIO.setup(A1, GPIO.OUT)
GPIO.setup(A2, GPIO.OUT)
GPIO.setup(A3, GPIO.OUT)
GPIO.setup(A4, GPIO.OUT)
GPIO.setup(A5, GPIO.OUT)
GPIO.setup(A6, GPIO.OUT)
GPIO.setup(A7, GPIO.OUT)

def activateRELAY(relay,setting):
	if(relay==0):
		GPIO.output(A0,setting)
	if(relay==1):
		GPIO.output(A1,setting)
	if(relay==2):
		GPIO.output(A2,setting) 
	if(relay==3):
		GPIO.output(A3,setting) 
	if(relay==4):
		GPIO.output(A4,setting) 
	if(relay==5):
		GPIO.output(A5,setting) 
	if(relay==6):
		GPIO.output(A6,setting) 
	if(relay==7):
		GPIO.output(A7,setting)

def Blink(relayTimes,speed):
	for i in range(0,relayTimes):
		for j in range(0,8):
			activateRELAY(j,False)


def main(argv):
	Blink(1,0)


if __name__ == "__main__":
	main(sys.argv[1:])

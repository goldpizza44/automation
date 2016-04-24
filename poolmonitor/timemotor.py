#!/usr/bin/python

import RPi.GPIO as GPIO
import time
import sys,getopt

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

def activateRELAY(relay,setting):

        # These are negative logic.
        if(relay==0):
                GPIO.output(A0, not setting)
        if(relay==1):
                GPIO.output(A1, not setting)
        if(relay==2):
                GPIO.output(A2, not setting)
        if(relay==3):
                GPIO.output(A3, not setting)
        if(relay==4):
                GPIO.output(A4, not setting)
        if(relay==5):
                GPIO.output(A5, not setting)
        if(relay==6):
                GPIO.output(A6, not setting)
        if(relay==7):
                GPIO.output(A7, not setting)

        # These are positive logic
        if(relay==8):
                GPIO.output(A8,setting)
        if(relay==9):
                GPIO.output(A9,setting)
        if(relay==10):
                GPIO.output(A10,setting)
        if(relay==11):
                GPIO.output(A11,setting)
        if(relay==12):
                GPIO.output(A12,setting)
        if(relay==13):
                GPIO.output(A13,setting)
        if(relay==14):
                GPIO.output(A14,setting)

def main(argv):
	activateRELAY(0,True)
	for c in range(35):

		time.sleep(1)
		print c

	activateRELAY(0,False)

	time.sleep(10)

        activateRELAY(1,True) 
	for c in range(35):
                time.sleep(1)
                print c

        activateRELAY(1,False)



if __name__ == "__main__":
        main(sys.argv[1:])


#!/usr/bin/python

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

def RCtime(pin):
	count=0
	GPIO.setup(pin,GPIO.OUT)
	GPIO.output(pin,GPIO.LOW)
	time.sleep(0.1)

	GPIO.setup(pin,GPIO.IN)
	while(GPIO.input(pin) == GPIO.LOW):
		count+=1

	return(count)

while True:
	print RCtime(23)
	time.sleep(1)



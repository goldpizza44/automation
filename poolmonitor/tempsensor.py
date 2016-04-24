#!/usr/bin/python
#
# Customized Home Automation 
#
# Copyright (C) 2016, David Goldfarb
#
# Distributed under the terms of the GNU General Public License
#
# Written by David Goldfarb
#

import time
import os
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
DEBUG=1

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

SPICLK=23
SPIMISO=21
SPIMOSI=19
SPICS=15

GPIO.setup(SPIMOSI,GPIO.OUT)
GPIO.setup(SPIMISO,GPIO.IN)
GPIO.setup(SPICLK,GPIO.OUT)
GPIO.setup(SPICS,GPIO.OUT)

TempADC=0

while True:
	temp=readadc(TempADC,SPICLK,SPIMOSI,SPIMISO,SPICS)
	print temp
	time.sleep(1)


#!/usr/bin/python
import RPi.GPIO as GPIO
import time

# Pin Definitions
SPICLK = 23
SPIMISO = 21
SPIMOSI = 19
SPICS = 15

# Setup GPIO
GPIO.setmode(GPIO.BOARD)

GPIO.setup(SPIMOSI, GPIO.OUT)
GPIO.setup(SPIMISO, GPIO.IN)
GPIO.setup(SPICLK, GPIO.OUT)
GPIO.setup(SPICS, GPIO.OUT)

def readadc(adcnum, clockpin, mosipin, misopin, cspin):
    if adcnum > 7 or adcnum < 0:
        return -1

    GPIO.output(cspin, True)

    GPIO.output(clockpin, False)  # start clock low
    GPIO.output(cspin, False)     # bring CS low

    commandout = adcnum
    commandout |= 0x18  # start bit + single-ended bit
    commandout <<= 3    # we only need to send 5 bits here
    for i in range(5):
        if (commandout & 0x80):
            GPIO.output(mosipin, True)
        else:
            GPIO.output(mosipin, False)
        commandout <<= 1
        GPIO.output(clockpin, True)
        GPIO.output(clockpin, False)

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

for i in range(10):
    raw_temp=readadc(0,23,19,21,15)
    raw_pressure=readadc(1,23,19,21,15)
    print('{}	{}'.format(raw_temp,raw_pressure))
    time.sleep(1)


GPIO.cleanup()

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
import sys,getopt
import poolctl

def Blink(relayTimes,speed):
	for i in range(0,relayTimes):
		for j in range(0,15):
			poolctl.activateRELAY(j,True)
			time.sleep(speed)
			poolctl.activateRELAY(j,False)

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
			print("poolctl.py -i iterations -s speed")
			sys.exit(3)


	if(iterations==0):
		iterations = int(raw_input("Enter total relayber of times to blink: "))

	if (speed==0.0):
		speed = float(raw_input("Enter length of each blink(seconds): "))

	print ("iterations: "+str(iterations))
	print ("speed: "+str(speed))

	Blink(iterations,speed)


if __name__ == "__main__":
	main(sys.argv[1:])

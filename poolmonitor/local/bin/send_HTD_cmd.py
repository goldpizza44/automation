#!/usr/bin/python
#
# Customized Home Automation 
#
# Copyright (C) 2017, David Goldfarb
#
# Distributed under the terms of the GNU General Public License
#
# Written by David Goldfarb
#

import socket
import sys
import binascii
import struct
import getopt

WHOLEHOUSEIP='172.16.2.191'
WHOLEHOUSEPORT=10006

cmd=[0x02, 0x00, 0x01, 0x04, 0x00, 0x00]
query=[0x02, 0x00, 0x01, 0x06, 0x00, 0x09]

allpwroff=  [0x02, 0x00, 0x01, 0x04, 0x39, 0x40]
allpwron=   [0x02, 0x00, 0x01, 0x04, 0x38, 0x3F]

outputzones={ 'patio':1,'kitchen':2,'diningroom':3,'theatre':4,'greatroom':5,'masterbedroom':6 }
inputsources={ 'kitchenpc':1,'greatroom':2,'masterbedroom':3,'tempmonitor':4,'theatre':5,'patio':6 }

cmdcodes={
	'volumeup':	0x09,
	'volumedown':	0x0A,
	'poweron':	0x20,
	'poweroff':	0x21,
	'mutetoggle':	0x22,
	'bassup':	0x26,
	'bassdown':	0x27,
	'trebleup':	0x28,
	'trebledown':	0x29,
	'balanceright':	0x2a,
	'balanceleft':	0x2b,
	'partymode1':   0x3a,
	'partymode2':   0x3b,
	'partymode3':   0x3c,
	'partymode4':   0x3d,
	'partymode5':   0x3e,
	'partymode6':   0x3f
}

def helpmsg():
	print >> sys.stderr, """
USAGE: ./send_HTD_cmd.py -a action [ -z zone ] [ -s source ]
	actions:   setinput, query, allpoweron,allpoweroff,
                   volumeup, volumedown, poweron, poweroff, mutetoggle,
                   bassup, bassdown, trebleup, trebledown, balanceright, balanceleft, 
	           partymode1, partymode2, partymode3, partymode4, partymode5, partymode6

	zones:     patio kitchen diningroom theatre greatroom masterbedroom

	sources:   kitchenPC greatroom masterbedroom tempmonitor theatre patio
"""
	sys.exit()

def setInputChannel(zone,source):
	inputcmd=cmd
	inputcmd[2]=outputzones[zone]
	inputcmd[4]=inputsources[source]+2
	# Byte 5 should be the sum of bytes 0->4.
	# Bytes 0,1,3 are fixed and sum to 6, and byte 4 is 2 more than the source
	inputcmd[5]=outputzones[zone]+inputsources[source]+8
	return (struct.pack('bbbbbb',*inputcmd))

def setAction(zone,action):
	inputcmd=cmd
	inputcmd[2]=outputzones[zone]
	inputcmd[4]=cmdcodes[action]
	# Byte 5 should be the sum of bytes 0->4.
	# Bytes 0,1,3 are fixed and sum to 6, which is a constant added to bytes 2,4
	inputcmd[5]=cmdcodes[action]+outputzones[zone]+6
	return (struct.pack('bbbbbb',*inputcmd))

#s=setInputChannel('patio','kitchenPC')
#s=setAction('masterbedroom','BassUp')
#print >>sys.stderr,  binascii.hexlify(s)

def main(argv):
	try: 
		opts,args=getopt.getopt(argv,"z:a:s:d",["zone=","action=","source="])
	except getopt.GetoptError:
		print("send_HTD_cmd.py [-d] -z zone -a action [ -s source ]")
		helpmsg()
	
	zone=''
	action=''
	source=''
	s=''
	debug=0
	
	for opt, arg in opts:
		if opt == '-z':
			zone=arg.lower()
		elif opt == '-a':
			action=arg.lower()
		elif opt == '-s':
			source=arg.lower()
		elif opt == '-d':
			debug=1

	# These actions don't need a zone
	if action == "query":
		s=struct.pack('bbbbbb',*query)

	elif action == "allpwron":
		s=struct.pack('bbbbbb',*allpwron)

	elif action == "allpwroff":
		s=struct.pack('bbbbbb',*allpwroff)

	else:
		# Check for a valid zone
		if not zone in outputzones:
			print >>sys.stderr, "send_HTD_cmd.py: Error unknown zone "+zone
			helpmsg()
		
		# Check the Action
		if action == "setinput":
			if not source in inputsources:
				print >>sys.stderr, "send_HTD_cmd.py: Error SetSource to unknown source"
				helpmsg()
			else:
				s=setInputChannel(zone,source)

		elif action in cmdcodes:
			s=setAction(zone,action)
		else:
			print >>sys.stderr, "send_HTD_cmd.py: Error unknown Action "+action
			helpmsg()
		
	if debug: print >>sys.stderr, "Sending: "+ binascii.hexlify(s)

	# We have the action string, send to the HTD and wait for the response

	# Create a TCP/IP socket
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Connect the socket to the port where the server is listening
	server_address = (WHOLEHOUSEIP,WHOLEHOUSEPORT)
	# print >>sys.stderr, 'connecting to %s port %s' % server_address
	sock.connect(server_address)

	try:
    
 		# Send data
		sock.sendall(s)

		# Look for the response
	        data = sock.recv(512)
		if debug: print >> sys.stderr, "Received {} Bytes\n".format( len(data))
		print "<audio>"
		for i in range(7):
			if (len(data) > 14*i):
				t=data[14*i : (14*i)+14]
				if debug: print >>sys.stderr, "Received: "+ binascii.hexlify(t)
				dataunpacked=struct.unpack('hbbbbbbbbbbbb',t)
				if dataunpacked[2]==5:
					for zone in outputzones:
						if dataunpacked[1] == outputzones[zone]:break
	
					for source in inputsources:
						if dataunpacked[7]==(inputsources[source]-1):break
		
					if dataunpacked[3]&0x80: power='on'
					else : power='off'
					
					if dataunpacked[3]&0x40: mute='on'
					else : mute='off'
					
					
					volume=60+dataunpacked[8]
	

					print "<audiozone zone=\"{}\" source=\"{}\" volume=\"{}\" power=\"{}\" mute=\"{}\"/>".format(zone,source,volume,power,mute)
					
		print "</audio>"
	finally:
		sock.close()

if __name__ == "__main__":
	main(sys.argv[1:])
	exit()

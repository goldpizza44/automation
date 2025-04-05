#!/usr/bin/python3
# -------------------------------------------------------------------------------
#
#  X10mqtt Home Assistant Addon
#
#   This script allows for bridging between MQTT and X10.
#
#   It utilizes the 'heyu' command (https://www.heyu.org) for X10 control
#   and monitoring.
#
# -------------------------------------------------------------------------------


import paho.mqtt.client as mqtt
import re,os,subprocess,json

try:
  broker = os.environ['MQTTBROKER']
except:
  print("Defaulting to Broker 'localhost'")
  broker = 'localhost'
  
try:
  port = int(os.environ['MQTTPORT'])
except:
  print("Defaulting to MQTT Broker port 1883")
  port = 1883

cmdtopic='x10/cmd'
stattopic='x10/stat'
rcvihc = ""

X10DEVICES=[]

CONFIGFILE=open("/usr/local/etc/heyu/x10.conf")
for line in CONFIGFILE:
  p=line.split()
  if len(p) > 2 and p[0].lower()=='alias':
    X10DEVICES.append({'alias':p[1],'housecode':p[2],'type':p[3]})
CONFIGFILE.close()

X10ALIAS=[ x['alias'] for x in X10DEVICES ]
for i in X10ALIAS:
  print(i)

# execute calls "heyu XX code" where XX is ON or OFF and code is "G2" or something defined in
# the /usr/local/etc/heyu/x10.conf file
def execute(client, cmd, housecode):
  heyucmd = cmd
  print("About to run: ",["heyu", heyucmd.lower(), housecode.lower()])
  result = subprocess.call(["/usr/local/bin/heyu", heyucmd.lower(), housecode.lower()])
  if result:
    print("Error running heyu, return code: "+str(result))
  print("Device Status Update: "+stattopic+"/"+housecode.lower())
  client.publish(stattopic+"/"+housecode.lower(),cmd.upper(),retain=True)
  return (result)

# monitor runs "heyu monitor" to listen for changes on X10 devices
def monitor():
    popen = subprocess.Popen(["heyu","monitor"], stdout=subprocess.PIPE, universal_newlines=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)
#
# The monitor lines are broken out into 2 lines for one event:
#   rcvi addr unit - Declares the full unit number
#   rcvi func - The function on that unit
#

#
# Monitor rcvi addr unit - save the unit address in a variable for later
#
# Argument:  housecode, which is the housecode involved.  This is captured from the regex in the main loop and passed.
#

def rcviaddr(housecode):
  global rcvihc
  # Store the received housecode for when rcvifunc is received
  rcvihc = housecode

#
# Monitor rcvi func - the function that was applied to the housecode
#
# This happens after the 'rcvi addr unit', so the housecode that is stored
# from that is what is used.
#
# Argument:  func, which is the function (On or Off).  This is captured from the regex in the main loop and passed.
#

def rcvifunc(client,func):
  global rcvihc
  if rcvihc:
   print("Remote status change, publishing stat update: "+stattopic+"/"+rcvihc.lower()+" is now "+func.upper())
   client.publish(stattopic+"/"+rcvihc.lower(),func.upper(), retain=True)
   rcvihc = ""

#
# Define MQTT Connect Callback
#

def on_connect (client, userdata, flags, rc):

  # Set up MQTT subscription
  if rc:
    print("Error connecting to MQTT broker rc "+str(rc))

  print("Connected to MQTT broker, result code "+str(rc))
  client.subscribe(cmdtopic+"/+")
  for DEVICE in X10DEVICES:
    discovery_topic='homeassistant/light/'+DEVICE["alias"]+'/config'
    payload = {
      "name"          : DEVICE["alias"],
      "command_topic" : 'x10/cmd/'+DEVICE["alias"],
      "payload_on": "ON",
      "payload_off": "OFF",
      "unique_id": DEVICE["alias"],
      "device": {
        "identifiers": [DEVICE["alias"]],
        "name": DEVICE["alias"],
        "model": DEVICE["type"],
        "manufacturer": "X10"
      }
    }
    print(discovery_topic)
    print(payload)
    client.publish(discovery_topic, json.dumps(payload), qos=1, retain=True  )

#
# Callback for MQTT message received
#

def on_message(client, userdata, message):

  # Determine the device from the topic
  # Topics are cmdtopic/dev, e.g. 'x10/cmd/A1'
  # So the last part is the device we want to control

  command = str(message.payload.decode('utf-8')).upper()
  print("Received: "+message.topic+" "+command)
  topiclist = message.topic.split("/")

  # Get the homecode and convert it to lower case
  hc = topiclist[len(topiclist)-1].lower()


  # Check that everything is right
  hcpattern = re.compile("^[a-p][0-9]+$")
  if command in ["ON", "OFF"] and (hcpattern.match(hc) or (hc in X10ALIAS)):
#  if command in ["ON", "OFF"]:
    print("Sending X10 command to homecode "+hc)
    result = execute(client, command, hc)
  else:
    print("Invalid command or home code")

# ---------------------------
# Main program
# ---------------------------

# MQTT connect


print("Establishing MQTT to "+broker+" port "+str(port)+"...")
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Check if mqttuser or mqttpass is not blank
# If not, then configure the username and password

# Not currently using a user/pass on the broker...may do this in future
mqttuser=None
mqttpass=None
if mqttuser and mqttpass:
  print("(Using MQTT username "+mqttuser+")")
  client.username_pw_set(mqttuser,mqttpass)

try:
  client.connect(broker,port)
except:
  print("Connection failed. Make sure broker, port, and user is defined correctly")
  exit(1)


# Start the MQTT loop

print("Waiting for MQTT messages and monitoring for remote changes")
client.loop_start()

# We run 'heyu monitor' in the background to monitor for any X10 changes outside of us (e.g. X10 remotes)
# This way, we can send MQTT status changes if something does change.

# Regular expressions used to catch X10 updates, e.g. from X10 remotes

rercviaddr = re.compile(r"rcvi addr unit.+hu ([A-P][0-9]+)")
rercvifunc = re.compile(r"rcvi func.*(On|Off) :")


# Start the monitor process, which runs all the time.
# Catch any updates we care about so we can handle sending status updates via MQTT

for line in monitor():
  addrsearch = rercviaddr.search(line)
  funcsearch = rercvifunc.search(line)
  if addrsearch:
    rcviaddr(str(addrsearch.group(1)))
  if funcsearch:
    rcvifunc(client,str(funcsearch.group(1)))

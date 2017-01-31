#!/usr/bin/python -u

import json
import sys
import xml.etree.cElementTree as ET

jdata=sys.stdin.readlines()

settingXML=ET.Element("settings")

for j in jdata:
	jdata1=json.loads(j)	

	for s in jdata1:
		settingType=ET.SubElement(settingXML,s)
		for f in jdata1[s]:
			setting=ET.SubElement(settingType,'setting')
			setting.set('name',f)
			setting.text=str(jdata1[s][f])

		
tree=ET.ElementTree(settingXML)
tree.write(sys.stdout)

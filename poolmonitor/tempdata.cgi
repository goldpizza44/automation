#!/bin/bash

cat <<!
Content-Type: text/event-stream
Cache-Control: no-cache

!

tail -f /var/www/html/tempdata.csv|gawk -F, '{
	printf("Content-Type: text/event-stream\n")
	printf("Cache-Control: no-cache\n\n")

	printf("data: {\"timestamp\":\"%s\", \"humidity\":\"%s\", \"patiotemp\":\"%s\", \"pumptemp\":\"%s\", \"pooltemp\":\"%s\" }\n\n",$1,$3,$4,$5,$6);
	fflush()
}'





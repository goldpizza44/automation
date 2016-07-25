#!/bin/bash
#
# Customized Home Automation 
#
# Copyright (C) 2016, David Goldfarb
#
# Distributed under the terms of the GNU General Public License
#
# Written by David Goldfarb
#

cat <<!
Content-Type: application/json
Cache-Control: no-cache

!
export DataSize=600

IFS='&'
for i in $QUERY_STRING
do
        export $i
done
unset IFS

ssh odroid@tempmonitor.goldfarbs.net "tail -${DataSize} /var/www/html/tempdata.csv" | gawk -F, '
BEGIN {
	printf("{ \"temperatures\": [\n")
}
{
	printf("{ \"timestamp\":\"%s\", \"d\" : { \"AlexanderBedroom\":%.2f, \"GuestBedroom\":%.2f, \"NikitaBedroom\":%.2f, \"DanielBedroom\":%.2f , \"UpstairsHall\":%.2f , \"KitchenDining\":%.2f , \"GreatRoomOffice\":%.2f } },\n",$1,$3,$4,$5,$6,$7,$8,$9);

}
END {
	printf("{ \"end\":0 } ]}\n")
}'

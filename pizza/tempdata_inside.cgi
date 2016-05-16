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

ssh odroid@odroid64.goldfarbs.net "tail -${DataSize} /var/www/html/tempdata.csv" | gawk -F, '
BEGIN {
	printf("{ \"temperatures\": [\n")
}
{
	printf("{ \"timestamp\":\"%s\", \"d\" : { \"AlexanderBedroom\":%s, \"GuestBedroom\":%s, \"NikitaBedroom\":%s, \"DanielBedroom\":%s , \"UpstairsHall\":%s } },\n",$1,$3,$4,$5,$6,$7);

}
END {
	printf("{ \"end\":0 } ]}\n")
}'

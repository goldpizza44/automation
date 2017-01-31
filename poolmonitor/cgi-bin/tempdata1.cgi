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

tail -${DataSize} /var/www/html/tempdata.csv | gawk -F, '
BEGIN {
	printf("{ \"temperatures\": [\n")
}
{
	printf("{ \"timestamp\":\"%s\", \"d\" : { \"humidity\":%s, \"patiotemp\":%s, \"pumptemp\":%s, \"pooltemp\":%s , \"filterpressure\":%s } },\n",$1,$3,$4,$5,$6,$9==""?0:$9);

}
END {
	printf("{ \"end\":0 } ]}\n")
}'

#!/bin/bash

DATE=$(date "+%Y/%m/%d")
TIME=$(date "+%H:%M")

export StartDate=$DATE
export EndDate=$DATE

IFS='&'
for i in $QUERY_STRING
do
        export $i
done
unset IFS

# Replace %2F with a '/'
StartDate=${StartDate//\%2F//}
EndDate=${EndDate//\%2F//}


cat <<!
Content-type: text/html

<HTML><BODY>
<BASE href="/pool/">
<H1>Goldfarb's Pool</H1>
Access <a href="tempdata.csv">tempdata.csv</a>

!
tail -1 /var/www/html/tempdata.csv | awk -F, '
{
	printf("The Current temperatures are:\n")
	printf("<ul>\n")
	printf("<li>DS18B20    - %s</li>\n",$5)
	printf("<li>DHT22      - %s</li>\n",$4)
	printf("<li>THERMISTOR - %s</li>\n",$6)
	printf("</ul>\n")
	printf("<P>The Current Humidity is: %s%%<P>\n",$3)
}
'
echo "<P>Chart for $StartDate to $EndDate<P>"
mkdir -p /var/www/html/tmp/chart.$$
cd /var/www/html/tmp/chart.$$

# Convert the data to average per minute
awk -F, -v StartSec=$(date '+%s' --date="$StartDate 00:00:00") -v EndSec=$(date '+%s' --date="$EndDate 23:59:59") '
BEGIN {
	getline
	for(i=1;i<=NF;i++) col[$i]=i
}
{
	minute=$1
	sub(/:..$/,"",minute)
	if(minute != lastminute) {
		if(lastminute != "") printf("%s,%s,%s,%s\n",
			lastminute,
			dht22/count,
			ds18b20/count,
			thermistor/count)
		dht22=ds18b20=thermistor=count=0
		lastminute=minute
	}

	dht22 += $(col["DHT22_F"])
	ds18b20 += $(col["DS18B20_F"])
	thermistor += $(col["THERMISTOR"])
	count++

}
' /var/www/html/tempdata.csv > temp.csv 2> awk.error

LASTINTERVAL=$(tail -1 temp.csv|awk -F, '{print $1}')

# I want  a maximum of 50 X-tags...need to calculate the number of  intervals based on data

cat <<!  > temp.plot
set terminal png size 1200,1000
set output "temp.png"
set datafile separator ","
set style data line
set xdata time
set x2data time
set timefmt "%Y/%m/%d %H:%M:%S"
set autoscale
set xrange ["$(date '+%Y/%m/%d 00:00:00' --date $StartDate)":"${LASTINTERVAL}"]
set xtics out rotate by 45 offset -9,-5.5 "$(date '+%Y/%m/%d 00:00:00' --date $StartDate)",1800
set ytics out
#set size 1.5,1.5
set title "Temperature at the Goldfarbs\n"
set ylabel "Fahrenheit"
set format x "%Y/%m/%d %H:%M"
set format y "%4.0f F"
set grid 

#set key horizontal
#set key outside

#set key off
#set nokey
#set format x2 ""
#set x2tics rotate
set border
set bmargin 20
#set lmargin at screen 0.15
set rmargin at screen 1
plot "temp.csv" using 1:2 title "DHT22" w l lw  4 ,\\
"temp.csv" using 1:3 title "DS18B20" w l lw  4 ,\\
"temp.csv" using 1:4 title "THERMISTOR" w l lw  4 
!

gnuplot < temp.plot

echo "<IMG SRC=\"tmp/chart.$$/temp.png\">"

echo "</BODY></HTML>"



#!/bin/bash

DATE=$(date "+%Y/%m/%d")
TIME=$(date "+%H:%M")

export StartDate="$DATE 00:00:00"
export EndDate="$DATE  23:59:59"

IFS='&'
for i in $QUERY_STRING
do
        export $i
done
unset IFS

# Replace %2F with a '/'
StartDate=${StartDate//\%2F//}
StartDate=${StartDate//\%20/ }
EndDate=${EndDate//\%2F//}
EndDate=${EndDate//\%20/ }

cat <<!
Content-type: text/html

<HTML>
<BODY style="font-family: verdana">
<BASE href="/pool/">
<H1>Goldfarb's Pool</H1>

!
tail -1 /var/www/html/tempdata.csv | awk -F, '
{
	printf("<table width=\"100%%\" border=\"5\"><tr>")
	printf("<td><center>Office Patio Temp<br><b><font color=\"red\"   size=\"15\">%s F</font></b></center></td>\n",$4)
	printf("<td><center>Pump Area Temp<br>   <b><font color=\"green\" size=\"15\">%s F</font></b></center></td>\n",$5)
	printf("<td><center>Pool Water Temp<br>  <b><font color=\"blue\"  size=\"15\">%s F</font></b></center></td>\n",$6)
	printf("<tr></table>\n")
	printf("<P>The Current Humidity is: %s%%<P>\n",$3)
}
'
echo 'Access <a href="tempdata.csv">tempdata.csv</a>'
echo "<P>Chart for $StartDate to $EndDate<P>"
mkdir -p /var/www/html/tmp/chart.$$
cd /var/www/html/tmp/chart.$$

# Convert the data to average per minute
awk -F, -v StartSec=$(date '+%s' --date="$StartDate") -v EndSec=$(date '+%s' --date="$EndDate") '
BEGIN {
	getline
	for(i=1;i<=NF;i++) col[$i]=i
	StartDate=strftime("%Y/%m/%d",StartSec)
	STARTFOUND=0
}
STARTFOUND==0 && $1 !~ StartDate {next}
{
	sec=$1
	gsub(/[\/:]/," ",sec)
	epochsec=mktime(sec)
}
epochsec > StartSec && epochsec <= EndSec {
	STARTFOUND=1
	minute=$1
	sub(/:..$/,"",minute)
	if(minute != lastminute) {
		if(lastminute != "") printf("%s,%s,%s,%s,%s\n",
			lastminute,
			dht22humid/count,
			dht22/count,
			ds18b20/count,
			thermistor/count)
		dht22=dht22humid=ds18b20=thermistor=count=0
		lastminute=minute
	}

	dht22       += $(col["DHT22_F"])
	dht22humid  += $(col["HUMIDITY"])
	ds18b20     += $(col["DS18B20_F"])
	thermistor  += $(col["THERMISTOR"])
	count++

}
' /var/www/html/tempdata.csv > temp.csv 2> awk.error

FIRSTINTERVAL=$(head -1 temp.csv|awk -F, '{print $1}')
LASTINTERVAL=$(tail -1 temp.csv|awk -F, '{print $1}')
NUMINTERVALS=$(wc -l temp.csv)

# I want  a maximum of 30 X-tags...need to calculate the number of  intervals based on data
# Number of intervals * 60 seconds divided by 30 (ie multiply intervals times 2) gives the number of seconds 
# between tags, and then round that to  a multiple of 15 minutes (900 seconds)

eval $(gawk -F, '
NR==1 { printf("export FIRSTINTERVAL=\"%s\";",$1) }
END {
	secs_per_interval=(NR*60)/30
	normalized_secs_per_interval=(int(secs_per_interval/900)+1)*900
	printf("export LASTINTERVAL=\"%s\";export INTERVALSECS=%s\n",$1,normalized_secs_per_interval)
}' temp.csv)

cat <<!  > temp.plot
set terminal png size 1200,1000
set output "temp.png"
set datafile separator ","
set style data line
set xdata time
set x2data time
set timefmt "%Y/%m/%d %H:%M:%S"
set autoscale
set xrange ["${FIRSTINTERVAL}":"${LASTINTERVAL}"]
set y2range [0:100]
set ytics out
set y2tics out
#set xtics out rotate by 45 offset -9,-5.5 "$(date '+%Y/%m/%d 00:00:00' --date='$StartDate')",1800
set xtics out rotate by 45 offset -9,-5.5 "${FIRSTINTERVAL}",${INTERVALSECS}
#set size 1.5,1.5
set title "Temperature at the Goldfarbs\n"
set ylabel "Fahrenheit"
set y2label "% Humidity"
set format x "%Y/%m/%d %H:%M"
set format y "%4.0f F"
set format y2 "%4.0f %%"
set grid  x y

#set key horizontal
#set key outside

set key top above
#set nokey
#set format x2 ""
#set x2tics rotate
set border
set bmargin 20
#set lmargin at screen 0.15
#set rmargin at screen 1
plot "temp.csv" using 1:3 title "Office Patio Temp" w l lw  4 ,\\
"temp.csv" using 1:4 title "Pump Area Temp" w l lw  4 ,\\
"temp.csv" using 1:5 title "Pool Water Temp" w l lw  4 , \\
"temp.csv" using 1:2 title "Humidity" axes x1y2 w l lw  4
!

gnuplot < temp.plot

echo "<IMG SRC=\"tmp/chart.$$/temp.png\">"

echo "</BODY></HTML>"


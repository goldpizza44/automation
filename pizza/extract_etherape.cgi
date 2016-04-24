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

if [ "${REMOTE_ADDR%.*}" != 172.16.2 -a "${REMOTE_ADDR}" != 127.0.0.1 -a "${REMOTE_ADDR%%.*}" != 208 ] 
then
	cat <<!
Content-type: text/html

<HTML><BODY><H1>ERROR1</H1>$REMOTE_ADDR</BODY></HTML>
!
	exit
fi

DATE=$(date "+%Y/%m/%d")
TIME=$(date "+%H:%M")

IFS='&'
for i in $QUERY_STRING
do
	export $i
done
unset IFS

# Replace %2F with a '/'
StartDate=${StartDate//\%2F//}
EndDate=${EndDate//\%2F//}

if [ -n "$Target"  -a -n "$StartDate" -a -n "$EndDate" ]
then
	SD=${StartDate//\/}
	ED=${EndDate//\/}
	OUTCSV=/var/www/html/etherape/${Target}-${SD}-${ED}.csv
	OUTPLOT=/var/www/html/etherape/${Target}-${SD}-${ED}.plot
	OUTPNG=/var/www/html/etherape/${Target}-${SD}-${ED}.png
	

	[[ $(uname -n) == pizza* ]] && FILEPATH=/var/www/html/goldfarb/html || FILEPATH=/var/www/html
	
	FILE=$(date "+etherape%Y%mxx.csv" --date=$SD)
	
	/usr/local/bin/extract_etherape_csv $StartDate $EndDate $Target $FILEPATH/$FILE > $OUTCSV
fi

if [ "$BUTTON" = "CSV" ]
then
	cat <<!
Content-type: text/csv
Content-disposition: attachment; filename="${OUTCSV##*/}";

!
	echo "TIMESTAMP,IP,NAME,CUMULATIVE,DELTA"
	cat $OUTCSV
	exit
else

	StartDate=${StartDate:-$(date "+%Y/%m/01")}
	EndDate=${EndDate:-${DATE}}
	Target=${Target:-ALL}

	cat <<! | sed "s%<option>$Target%<option selected=\"selected\">$Target%"
Content-type: text/html

<HTML><HEAD><TITLE>Extract Etherape</TITLE></HEAD><BODY>
<FORM method=get action=extract_etherape.cgi>
<H1>Chart Internet Usage</H1>
<select Name="Target">
<option>Select Target</option>
<option>Nikita</option>
<option>Daniel</option>
<option>Alex</option>
<option>Elena</option>
<option>David</option>
<option>KIDS</option>
<option>FAMILY</option>
<option>TV</option>
<option>OTHER</option>
<option>ALL</option>
</select>
<select Name="StartDate">
<option>Select Date</option>
!

	for i in $(seq 1 200)
	do
		date "+<option>%Y/%m/%d</option>" --date=-${i}days | sed "s%<option>$StartDate%<option selected=\"selected\">$StartDate%"
	done

	echo '</select><select Name="EndDate"><option>Select Date</option>'

	for i in $(seq 0 200)
	do
		date "+<option>%Y/%m/%d</option>" --date=-${i}days | sed "s%<option>$EndDate%<option selected=\"selected\">$EndDate%"
	done

	cat <<!
</select>
<P>
<INPUT TYPE=SUBMIT NAME=BUTTON VALUE="CHART">
<INPUT TYPE=SUBMIT NAME=BUTTON VALUE="CSV">
</FORM>
<P>
!
	
	if [ "$BUTTON" = "CHART" ]
	then
		let SECS=$(date '+%s' --date=$EndDate)-$(date '+%s' --date=$StartDate)
		TICSPACE=$SECS
		cd /var/www/html/etherape

		OUTCSV=${OUTCSV##*/}


		FILES=( $(gawk -F, '$NF > 0 {F=$3"."FILENAME;FILES[F]++;print $0 > F }END{for (F in FILES) if (F ~ /^TOTAL/|| F ~ /^OTHER/ ) { print F;delete FILES[F]}for (F in FILES) print F }' $OUTCSV) )

# Find the TOTAL file
for i in $(seq 0 $((${#FILES[@]}-1)))
do
	if [[ ${FILES[$i]} == TOTAL* ]]
	then
		eval $(tail -n 1 ${FILES[$i]} | gawk -F, '
{
	printf("export TOTALLASTVALUE=%e;export TOTALLASTVALUEgb=%4.2f;export LASTTIMESTAMP=\"%s\";export twoFiftyLine=%s;",$4,$4/1000000000,$1,$4>200000000000?"YES":"NO")
}
')


		break
	fi
done
		cat <<! > $OUTPLOT

set terminal png size 1200,1000
set output "$OUTPNG"
set datafile separator ","
set style data line
set xdata time
set x2data time
set timefmt "%Y/%m/%d %H:%M:%S"
set xrange ["$(date '+%Y/%m/%d 00:00:00' --date $StartDate)":"$(date '+%Y/%m/%d 23:59:59' --date $EndDate)"]
#set size 1.5,1.5
set title "$Target Internet Usage\n$TOTALLASTVALUEgb Gbytes at\n$LASTTIMESTAMP"
set ylabel "Total Bytes"
#set y2label "Bytes per minute"
set format x "%Y/%m/%d %H:%M:%S"
set format y "%4.2s %cBytes"
#set ytics 0,10e+9,300e+9
set ytics 10e+9
set xtics rotate "$(date '+%Y/%m/%d 00:00:00' --date $StartDate)",86400,"$(date '+%Y/%m/%d 23:59:59' --date $EndDate)"
set grid ytics

set key horizontal
#set key outside

#set key off
#set nokey
#set format x2 ""
#set x2tics rotate
set border
set bmargin 20
set lmargin at screen 0
set rmargin at screen 1
#set label "$TOTALLASTVALUEgb Gbytes at\n$LASTTIMESTAMP" at "$(date '+%Y/%m/%d %H:%M:%S' --date $StartDate+12hours)",$TOTALLASTVALUE
!
if [ "$twoFiftyLine" != "YES" ]
then
	cat <<! >> $OUTPLOT
plot  "${FILES[0]}" using 1:4 title "${FILES[0]%.${OUTCSV}}" w l lw 4 \\
!
else
	cat <<! >> $OUTPLOT
f(x)=250e+9
plot f(x) title "250Gb limit" w l lw 4, "${FILES[0]}" using 1:4 title "${FILES[0]%.${OUTCSV}}" w l lw 4 \\
!
fi

for i in $(seq 1 $((${#FILES[@]}-1)))
do
	echo ",\"${FILES[$i]}\" using 1:4 title \"${FILES[$i]%.${OUTCSV}}\" \\" >> $OUTPLOT
done
cat <<! >> $OUTPLOT

!

		gnuplot < $OUTPLOT
		echo "<IMG SRC=\"/etherape/${OUTPNG##*/}\">"
	fi

	echo "</BODY></HTML>"

fi

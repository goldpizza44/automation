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
DATE=$(date "+%Y%m%d-%H%M")

if [ "${REMOTE_ADDR%.*}" != 172.16.2 -a "${REMOTE_ADDR}" != 127.0.0.1 ]
then
	cat <<!
Content-type: text/html

<HTML><BODY><H1>ERROR1</H1>$REMOTE_ADDR</BODY></HTML>
!
	exit
fi

IFS='&'
for i in $QUERY_STRING
do
	export $i
done
unset IFS

echo "Content-type: text/xml"
echo
echo "<HTML><BODY>"

echo $ACTION
case "$ACTION" in
ALL_LIGHTS_ON)
			ssh pi@poolmonitor "heyu on  exterior_front" 2>&1;
			ssh pi@poolmonitor "heyu on  exterior_rear" 2>&1;
			ssh pi@poolmonitor "heyu on  courtyard" 2>&1;
			ssh pi@poolmonitor "heyu on  exterior_ne" 2>&1;
			echo '{"lights":{"exterior_front":"on","exterior_rear":"on","courtyard":"on","exterior_ne":"on"}}'|/usr/local/bin/JSONtoXML.py
			;;
ALL_LIGHTS_OFF)
			ssh pi@poolmonitor "heyu off  exterior_front" 2>&1;
			ssh pi@poolmonitor "heyu off  exterior_rear" 2>&1;
			ssh pi@poolmonitor "heyu off  courtyard" 2>&1;
			ssh pi@poolmonitor "heyu off  exterior_ne" 2>&1;
			echo '{"lights":{"exterior_front":"off","exterior_rear":"off","courtyard":"off","exterior_ne":"off"}}'|/usr/local/bin/JSONtoXML.py
			;;
EXTERIOR_FRONT_ON)  ssh pi@poolmonitor "heyu on  exterior_front" 2>&1;;
EXTERIOR_FRONT_OFF) ssh pi@poolmonitor "heyu off exterior_front" 2>&1;;
EXTERIOR_NE_ON)     ssh pi@poolmonitor "heyu on  exterior_ne" 2>&1;;
EXTERIOR_NE_OFF)    ssh pi@poolmonitor "heyu off exterior_ne" 2>&1;;
EXTERIOR_REAR_ON)   ssh pi@poolmonitor "heyu on  exterior_rear" 2>&1;;
EXTERIOR_REAR_OFF)  ssh pi@poolmonitor "heyu off exterior_rear" 2>&1;;
SPRINKLERS_ON)      CURRENT_ZONE=$(cat /usr/local/etc/heyu/current_sprinkler_zone|gawk '{print $1}');
			let CURRENT_ZONE=CURRENT_ZONE+1                    				
			(( CURRENT_ZONE > 5 )) && CURRENT_ZONE=1
			ssh pi@poolmonitor "heyu on  sprinklers" 2>&1
			echo "$CURRENT_ZONE	ON" > /usr/local/etc/heyu/current_sprinkler_zone
                        echo "<sprinklers zone='$CURRENT_ZONE' state='ON'/>"
			;;
SPRINKLERS_OFF)     CURRENT_ZONE=$(cat /usr/local/etc/heyu/current_sprinkler_zone|gawk '{print $1}');
			ssh pi@poolmonitor "heyu off sprinklers" 2>&1
			echo "$CURRENT_ZONE	OFF" > /usr/local/etc/heyu/current_sprinkler_zone
                        echo "<sprinklers zone='$CURRENT_ZONE' state='OFF'/>"
			;;
SPRINKLER_ZONE)     CURRENT_ZONE=$(cat /usr/local/etc/heyu/current_sprinkler_zone|gawk '{print $1}');
			while (( CURRENT_ZONE != NEW_ZONE ))
			do
				ssh pi@poolmonitor "heyu on sprinklers" 2>&1;sleep 10;ssh pi@poolmonitor "heyu off sprinklers" 2>&1;sleep 10
				let CURRENT_ZONE=CURRENT_ZONE+1
				(( CURRENT_ZONE > 5 )) && CURRENT_ZONE=1
			done
			echo "$CURRENT_ZONE	ON" > /usr/local/etc/heyu/current_sprinkler_zone
			ssh pi@poolmonitor "heyu on sprinklers" 2>&1;
			;;
COURTYARD_ON)       ssh pi@poolmonitor "heyu on  courtyard" 2>&1;;
COURTYARD_OFF)      ssh pi@poolmonitor "heyu off courtyard" 2>&1;;
PONDPUMP_ON)        ssh pi@poolmonitor "heyu on  pond_pump" 2>&1;;
PONDPUMP_OFF)       ssh pi@poolmonitor "heyu off pond_pump" 2>&1;;
PONDLIGHTS_ON)      ssh pi@poolmonitor "heyu on  pond_lights" 2>&1;;
PONDLIGHTS_OFF)     ssh pi@poolmonitor "heyu off pond_lights" 2>&1;;
DAVIDLAMP_ON)       ssh pi@poolmonitor "heyu on  david_lamp" 2>&1;;
DAVIDLAMP_OFF)      ssh pi@poolmonitor "heyu off david_lamp" 2>&1;;
DAVIDLAMP_DIM)      ssh pi@poolmonitor "heyu dimb david_lamp $dimlevel" 2>&1;;
THEATRELAMP_ON)     ssh pi@poolmonitor "heyu on  theatre_lamp" 2>&1;;
THEATRELAMP_OFF)    ssh pi@poolmonitor "heyu off theatre_lamp" 2>&1;;
THEATRELAMP_DIM)    ssh pi@poolmonitor "heyu dimb theatre_lamp $dimlevel" 2>&1;;

POOL_LIGHT_ON)		POOLSETTING='{"poolSetting":{"PoolLight":"on"}}'		;;
POOL_LIGHT_OFF)		POOLSETTING='{"poolSetting":{"PoolLight":"off"}}'		;;

POOL_COLOR)		[ -z "$Color" -o "$Color" == 'off' ]  &&
			POOLSETTING='{"poolSetting":{"PoolLight":"off"}}' ||
			POOLSETTING='{"poolColor":{"Color":"'${Color}'"}}';;
			
TURN_ON_BUBBLER)	POOLSETTING='{"valveSetting":{"SpaPool": 180, "BubblerReturnSpray":90 } }'	;;
TURN_OFF_BUBBLER)	POOLSETTING='{"valveSetting":{"BubblerReturnSpray": 180} }'			;;
			
TURN_ON_SPRAY)		POOLSETTING='{"valveSetting":{"SpaPool": 180, "BubblerReturnSpray":0, "ReturnSpray":180 }  }'	;;
TURN_OFF_SPRAY)		POOLSETTING='{"valveSetting":{"ReturnSpray": 90 } }'			;;

TURN_ON_WATERFALL)	POOLSETTING='{"featureSetting":{"SpaFloor": "on" ,"SpaJets":"off"},"valveSetting":{"SpaPool": 0} }'	;;
TURN_OFF_WATERFALL)	POOLSETTING='{"valveSetting":{"SpaPool": 180} }'	;;

TURN_ON_RETURN)		POOLSETTING='{"valveSetting":{"SpaPool": 180,"BubblerReturnSpray":180,"ReturnSpray":90} }' ;;
TURN_OFF_RETURN)	POOLSETTING='{"valveSetting":{"SpaPool": 0} }'	;;

TURN_ON_SPA)		POOLSETTING='{"valveSetting":{"SpaPool": 0,"MainDrainSpaPool":0  } }'		;;
TURN_OFF_SPA)		POOLSETTING='{"valveSetting":{"SpaPool": 180,"MainDrainSpaPool":90 } }'	;;
TURN_ON_SPA_HEATER)	POOLSETTING='{"poolSetting":{"SpaHeater":"on", "MainPump":"on" },"valveSetting":{"SpaPool": 0,"MainDrainSpaPool":0  } }'		;;
TURN_OFF_SPA_HEATER)	POOLSETTING='{"poolSetting":{"SpaHeater":"off" } }'	;;
TURN_OFF_SPA_JETS)	POOLSETTING='{"valveSetting":{"SpaFloorJets":90} }' ;;
TURN_ON_SPA_JETS)	POOLSETTING='{"valveSetting":{"SpaFloorJets":0 ,"SpaPool":0} }' ;;
SPATEMP)		POOLSETTING='{"poolSetting":{"SpaTempTarget":'$temperature'}}' ;;

SPASCHEDULE)		
			ssh -q pi@poolmonitor "atrm \$(atq -q c|gawk '{print \$1}')" > /dev/null 2>&1
			if [ -n "$SpaReadyTime" -a -n "$temperature" ]
			then
				# Get the current water temperature and use that with the target temperature
				# to calculate the time needed for warming
				CURRENTTEMP=$(ssh -q pi@poolmonitor "tail -1 /var/www/html/tempdata.csv|cut -d, -f6")
				
				SpaOnTime=$(echo "$SpaReadyTime" | gawk -F: -v CURRENTTEMP=$CURRENTTEMP -v TARGETTEMP=$temperature '
{
	secs=($1*60*60)+($2*60)
	warmingTime=((TARGETTEMP-CURRENTTEMP)/0.13)*60
	secs=secs-warmingTime
	hours=int(secs/3600)
	mins=int((secs-(hours*3600))/60)
	printf("%s:%s",hours,mins)

}
')
				cat <<! | ssh pi@poolmonitor "at -q c $SpaOnTime > /dev/null 2>&1" 
echo '{"poolSetting":{"SpaHeater":"on","MainPump":"on" },"valveSetting":{"SpaPool": 0,"MainDrainSpaPool":0  } }' | /bin/nc localhost 2222
!
			fi
			if [ -n "$SpaStopTime" ]
			then
				cat <<! | ssh pi@poolmonitor "at -q c $SpaStopTime > /dev/null 2>&1"
echo '{"poolSetting":{"SpaHeater":"off","MainPump":"off" } }' | /bin/nc localhost 2222
!
			fi
			POOLSETTING='{"getSettings":"all"}';;

MAIN_PUMP_ON)		POOLSETTING='{"poolSetting":{"MainPump":"on" } }'		;;
MAIN_PUMP_OFF)		POOLSETTING='{"poolSetting":{"MainPump":"off"} }'		;;

DELETE_VMAIL)		/usr/local/bin/asterisk_vmail -m $mbox -M $msgnum -a DELETE;;
UPDATE_VMAIL)		NOTE=$(python -c "import sys, urllib as ul; print ul.unquote_plus(sys.argv[1])" "${Note}")
			/usr/local/bin/asterisk_vmail -m $mbox -M $msgnum -a UPDATE_NOTE -d "$NOTE"
			;;

GET_SETTINGS)		POOLSETTING='{"getSettings":"all"}';;
esac


(ssh pi@poolmonitor "heyu show config;heyu info") | gawk '
/HOUSECODE/ { HOUSECODE=$NF
	printf("<X10settings housecode=\"%s\">",HOUSECODE)
}

/ALIAS/ {alias[$3]=$2 }

/Status of monitored devices/ {
	split($NF,a,"");
	for(i=1;i<=16;i++) {
		onoff=a[18-i];
		CODE=HOUSECODE i
		if (alias[CODE] != "")
		printf("<setting name=\"%s\" code=\"%s\">%s</setting>\n",alias[CODE],CODE,onoff==0?"off":"on")
	}
}
END {printf("</X10settings>\n") }'

	# Get the voicemails as well.
	/usr/local/bin/asterisk_vmail
	cat /usr/local/etc/heyu/current_sprinkler_zone|gawk '{printf("<sprinklers zone=\"%s\" state=\"%s\"/>\n",$1,$2)}'
	/usr/local/bin/sunwait -p  26.251996N 80.259874W|gawk '
/Civil twilight starts/ {
	split($(NF-1),a,"");
	t=sprintf("1970 01 01 %d%d %d%d 00",a[1],a[2],a[3],a[4]);
	printf("<lightson time=\"%s\"/>\n",strftime("%H:%M",mktime(t)-900))
}'

[ -n "$POOLSETTING" ]&&echo "$POOLSETTING"|nc poolmonitor.goldfarbs.net 2222|/usr/local/bin/JSONtoXML.py
ssh pi@poolmonitor atq -q c |sort -n| gawk '{SpaStartTime=$5;getline;SpaStopTime=$5;printf("<SpaTimer on=\"%s\" off=\"%s\"/>\n",SpaStartTime,SpaStopTime)}'
echo "</BODY></HTML>"

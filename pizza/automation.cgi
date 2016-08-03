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
			heyu on  exterior_front 2>&1;
			heyu on  exterior_rear 2>&1;
			heyu on  courtyard 2>&1;
			heyu on  exterior_ne 2>&1;
			echo '{"lights":{"exterior_front":"on","exterior_rear":"on","courtyard":"on","exterior_ne":"on"}}'|/usr/local/bin/JSONtoXML.py
			;;
ALL_LIGHTS_OFF)
			heyu off  exterior_front 2>&1;
			heyu off  exterior_rear 2>&1;
			heyu off  courtyard 2>&1;
			heyu off  exterior_ne 2>&1;
			echo '{"lights":{"exterior_front":"off","exterior_rear":"off","courtyard":"off","exterior_ne":"off"}}'|/usr/local/bin/JSONtoXML.py
			;;
EXTERIOR_FRONT_ON)  heyu on  exterior_front 2>&1;;
EXTERIOR_FRONT_OFF) heyu off exterior_front 2>&1;;
EXTERIOR_NE_ON)     heyu on  exterior_ne 2>&1;;
EXTERIOR_NE_OFF)    heyu off exterior_ne 2>&1;;
EXTERIOR_REAR_ON)   heyu on  exterior_rear 2>&1;;
EXTERIOR_REAR_OFF)  heyu off exterior_rear 2>&1;;
SPRINKLERS_ON)      CURRENT_ZONE=$(cat /usr/local/etc/heyu/current_sprinkler_zone|gawk '{print $1}');
			let CURRENT_ZONE=CURRENT_ZONE+1                    				
			(( CURRENT_ZONE > 5 )) && CURRENT_ZONE=1
			heyu on  sprinklers 2>&1
			echo "$CURRENT_ZONE	ON" > /usr/local/etc/heyu/current_sprinkler_zone
                        echo "<sprinklers zone='$CURRENT_ZONE' state='ON'/>"
			;;
SPRINKLERS_OFF)     CURRENT_ZONE=$(cat /usr/local/etc/heyu/current_sprinkler_zone|gawk '{print $1}');
			heyu off sprinklers 2>&1
			echo "$CURRENT_ZONE	OFF" > /usr/local/etc/heyu/current_sprinkler_zone
                        echo "<sprinklers zone='$CURRENT_ZONE' state='OFF'/>"
			;;
SPRINKLER_ZONE)     CURRENT_ZONE=$(cat /usr/local/etc/heyu/current_sprinkler_zone|gawk '{print $1}');
			while (( CURRENT_ZONE != NEW_ZONE ))
			do
				heyu on sprinklers 2>&1;sleep 10;heyu off sprinklers 2>&1;sleep 10
				let CURRENT_ZONE=CURRENT_ZONE+1
				(( CURRENT_ZONE > 5 )) && CURRENT_ZONE=1
			done
			echo "$CURRENT_ZONE	ON" > /usr/local/etc/heyu/current_sprinkler_zone
			heyu on sprinklers 2>&1;
			;;
COURTYARD_ON)       heyu on  courtyard 2>&1;;
COURTYARD_OFF)      heyu off courtyard 2>&1;;
PONDPUMP_ON)        heyu on  pond_pump 2>&1;;
PONDPUMP_OFF)       heyu off pond_pump 2>&1;;
PONDLIGHTS_ON)      heyu on  pond_lights 2>&1;;
PONDLIGHTS_OFF)     heyu off pond_lights 2>&1;;
DAVIDLAMP_ON)       heyu on  david_lamp 2>&1;;
DAVIDLAMP_OFF)      heyu off david_lamp 2>&1;;
DAVIDLAMP_DIM)      heyu dimb david_lamp $dimlevel 2>&1;;
THEATRELAMP_ON)     heyu on  theatre_lamp 2>&1;;
THEATRELAMP_OFF)    heyu off theatre_lamp 2>&1;;
THEATRELAMP_DIM)    heyu dimb theatre_lamp $dimlevel 2>&1;;

POOL_LIGHT_ON)		POOLSETTING='{"poolSetting":{"PoolLight":"on"}}'		;;
POOL_LIGHT_OFF)		POOLSETTING='{"poolSetting":{"PoolLight":"off"}}'		;;

POOL_COLOR)		[ -z "$Color" -o "$Color" == 'off' ]  &&
			POOLSETTING='{"poolSetting":{"PoolLight":"off"}}' ||
			POOLSETTING='{"poolColor":{"Color":"'${Color}'"}}';;
			
TURN_ON_BUBBLER)	POOLSETTING='{"valveSetting":{"SpaPool": 180, "BubblerReturnSpray":90 } }'	;;
TURN_OFF_BUBBLER)	POOLSETTING='{"valveSetting":{"BubblerReturnSpray": 180} }'			;;
			
TURN_ON_SPRAY)		POOLSETTING='{"valveSetting":{"SpaPool": 180, "BubblerReturnSpray":0, "ReturnSpray":180 }  }'	;;
TURN_OFF_SPRAY)		POOLSETTING='{"featureSetting":{"Sprays":  "off"} }'			;;

TURN_ON_WATERFALL)	POOLSETTING='{"featureSetting":{"SpaFloor": "on" ,"SpaJets":"off"},"valveSetting":{"SpaPool": 0} }'	;;
TURN_OFF_WATERFALL)	POOLSETTING='{"valveSetting":{"SpaPool": 180} }'	;;

TURN_ON_RETURN)		POOLSETTING='{"valveSetting":{"SpaPool": 180,"BubblerReturnSpray":180,"ReturnSpray":90} }' ;;
TURN_OFF_RETURN)	POOLSETTING='{"valveSetting":{"SpaPool": 0} }'	;;

TURN_ON_SPA)		POOLSETTING='{"valveSetting":{"SpaPool": 0  } }'			;;
TURN_OFF_SPA)		POOLSETTING='{"valveSetting":{"SpaPool": 180} }'		;;

MAIN_PUMP_ON)		POOLSETTING='{"poolSetting":{"MainPump":"on" } }'		;;
MAIN_PUMP_OFF)		POOLSETTING='{"poolSetting":{"MainPump":"off"} }'		;;

DELETE_VMAIL)		/usr/local/bin/asterisk_vmail -m $mbox -M $msgnum -a DELETE;;
UPDATE_VMAIL)		NOTE=$(python -c "import sys, urllib as ul; print ul.unquote_plus(sys.argv[1])" "${Note}")
			/usr/local/bin/asterisk_vmail -m $mbox -M $msgnum -a UPDATE_NOTE -d "$NOTE"
			;;

GET_SETTINGS)		POOLSETTING='{"getSettings":"all"}';;
esac

(heyu show config;heyu info) | gawk '
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

echo "</BODY></HTML>"

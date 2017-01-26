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


export DataSize=720

IFS='&'
for i in $QUERY_STRING
do
        export $i
done
unset IFS

cat <<!
Content-Type: text/html

<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
  "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en-US"
  xml:lang="en-US">
<head>
    <link rel="stylesheet" href="http://pizza.goldfarbs.net/bootstrap/css/bootstrap.min.css"/>
    <link rel="stylesheet" href="http://pizza.goldfarbs.net/bootstrap/css/bootstrap-slider.min.css"/>
    <link rel="stylesheet" href="http://pizza.goldfarbs.net/bootstrap/css/bootstrap-clockpicker.min.css"/>
    <link rel="stylesheet" href="http://pizza.goldfarbs.net/bootstrap/css/horiz_tabscroll.css"/>
    <link rel="stylesheet" href="http://pizza.goldfarbs.net/fullcalendar/fullcalendar.css"/>
    <link rel="stylesheet" href="http://pizza.goldfarbs.net/fullcalendar/fullcalendar.print.css" media="print" />

    <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.0/jquery.min.js"></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/bootstrap/js/bootstrap.min.js"></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/bootstrap/js/bootstrap-slider.min.js"></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/bootstrap/js/modernizr.js"></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/bootstrap/js/bootstrap-clockpicker.min.js"></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/fullcalendar/lib/moment.min.js"></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/fullcalendar/fullcalendar.js"></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/RGraph/libraries/RGraph.common.core.js" ></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/RGraph/libraries/RGraph.line.js" ></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/RGraph/libraries/RGraph.common.key.js" ></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/RGraph/libraries/RGraph.drawing.xaxis.js" ></script>
    <title>Goldfarb Temperatures</title>

<script type="text/javascript">
var DimmerTimer;
var SpaTempTimer;
var SprinklerZone;
var SprinklerState;
var SprinklerTimer;
var SprinklerTimerObj;

var datasize=${DataSize}
var humidity_line, patiotemp_line, pumptemp_line, pooltemp_line,dateaxis;
var nikita_line,daniel_line,alexander_line,guest_line,hall_line,kitchendining_line,greatroom_line;
var labels = new Array (datasize);
var datelabels = new Array (datasize);
var firstload=1;
var disableGarageDoorSpeech=0
var spa_temp="?"
var spa_temp_target=0
var spa_heater_on_off
var vmailhead='<tr>'+
              '<th class="text-center">#</th>'+
              '<th class="text-center">Date/Time</th>'+
              '<th class="text-center">CallerID</th>'+
              '<th class="text-center">Duration (secs)</th>'+
              '</tr>';

for(var i=0;i<datasize;i++) datelabels[i]=''

function getOutSideTempData() {
    var xhttp=new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
	if (xhttp.readyState == 4 && xhttp.status == 200) {
	    var data=JSON.parse(xhttp.responseText)

	    if (data.temperatures) {
		drawOutside(data.temperatures)
		if (firstload==0) {
			setTimeout(getOutSideTempData,60000)
		} else {
			firstload=0
			var secstoNextMinute=(60- (new Date().getSeconds()) +5)*1000
			setTimeout(getOutSideTempData,secstoNextMinute)
		}
	    }
	}
    };
    var URL="http://pizza.goldfarbs.net/cgi-bin/tempdata1.cgi?DataSize="+datasize
    xhttp.open("GET", URL, true);
    xhttp.send();
}

function getInSideTempData() {
    var xhttp=new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
	if (xhttp.readyState == 4 && xhttp.status == 200) {
	    var data=JSON.parse(xhttp.responseText)

	    if (data.temperatures) {
                // There is a change the odriod is down and we dont get data
                if (data.temperatures.length > 1) drawInside(data.temperatures)
		if (firstload==0) {
			setTimeout(getInSideTempData,60000)
		} else {
			firstload=0
			var secstoNextMinute=(60- (new Date().getSeconds()) +5)*1000
			setTimeout(getInSideTempData,secstoNextMinute)
		}
	    }
	}
    };
    var URL="http://pizza.goldfarbs.net/cgi-bin/tempdata_inside.cgi?DataSize="+datasize
    xhttp.open("GET", URL, true);
    xhttp.send();
}

function createCharts() {
    var gutterLeft = 40, gutterRight = 40, gutterTop   = 100, gutterBottom = 75;
    var outside_ymax=110, outside_ymin=40, inside_ymax=80, inside_ymin=66;

    // This is used to initialize the charts (ie. tell them how many points to expect)
    var data= new Array(datasize);

    // Make and draw the background charts
    patiotemp_line = new RGraph.Line({
	id: 'cvs',
	data: data,
	options: {

	    title: "Temperatures\n",
	    titleBold: true,
	    titleSize: 12,
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: outside_ymax,
	    ymin: outside_ymin,
	    ylabelsCount: 7,
	    numyticks:7,
	    outofbounds: true,
	    backgroundGridAutofit: true,
	    backgroundGridAutofitNumvlines: 10,
	    backgroundGridAutofitNumhlines: 14,
//	    backgroundGridVlines: false,
	    backgroundGridBorder: false,
	    colors: [ 'Red','Green','Blue' ],
	    key: ['Patio Temp', 'Pump Temp', 'Water Temp' ],
	    keyPosition: 'gutter',
	    numxticks: 10,
	    tickmarks: null,
	    labels: labels,
//	    noaxes: true,
	    textSize: 12,
	    textAngle: 45,
	    textColor: '#aaa',
	    scaleZerostart: true
	}
    }).draw();

    pumptemp_line = new RGraph.Line({
	id: 'cvs',
	data: data,
	options: {
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: outside_ymax,
	    ymin: outside_ymin,
	    outofbounds: true,
	    backgroundGrid: false,
	    colors: [ 'green' ],
	    numxticks: 10,
	    tickmarks: null,
	    noaxes: true,
	    textColor: '#aaa',
	    ylabels: false,
	    scaleZerostart: true
	}
    }).draw();
    pooltemp_line = new RGraph.Line({
	id: 'cvs',
	data: data,
	options: {
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: outside_ymax,
	    ymin: outside_ymin,
	    outofbounds: true,
	    backgroundGrid: false,
	    colors: [ 'blue' ],
	    numxticks: 10,
	    tickmarks: null,
	    noaxes: true,
	    textColor: '#aaa',
	    ylabels: false,
	    scaleZerostart: true
	}
    }).draw();

    tempdateaxis = new RGraph.Drawing.XAxis({
	id: 'cvs',
	y: pooltemp_line.canvas.height - 25,
	options: {
	     labels: datelabels,
	     noxaxis: true,	
	     hmargin: 10,
	}
    }).draw()

    // Make and draw the chart
    humidity_line = new RGraph.Line({
	id: 'cvs2',
	data: data,
	options: {

	    title: "Humidity\n",
	    titleBold: true,
	    titleSize: 12,
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: 100,
	    ymin: 0,
	    ylabelsCount: 10,
	    numyticks:10,
	    outofbounds: true,
	    backgroundGridAutofit: true,
	    backgroundGridAutofitNumvlines: 10,
	    backgroundGridAutofitNumhlines: 10,
//	    backgroundGridVlines: false,
	    backgroundGridBorder: false,
	    colors: [ 'purple' ],
	    key: ['Humidity' ],
	    keyPosition: 'gutter',
	    numxticks: 10,
	    tickmarks: null,
	    labels: labels,
//	    noaxes: true,
	    textSize: 12,
	    textAngle: 45,
	    textColor: '#aaa',
	    scaleZerostart: true
	}
    }).draw();

    humiditydateaxis = new RGraph.Drawing.XAxis({
	id: 'cvs2',
	y: humidity_line.canvas.height - 25,
	options: {
	     labels: datelabels,
	     noxaxis: true,	
        }
    }).draw()

    // Make and draw the chart
    filterPressure_line = new RGraph.Line({
	id: 'cvs3',
	data: data,
	options: {

	    title: "Filter Pressure (PSI)\n",
	    titleBold: true,
	    titleSize: 12,
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: 30,
	    ymin: 0,
	    ylabelsCount: 10,
	    numyticks:10,
	    outofbounds: true,
	    backgroundGridAutofit: true,
	    backgroundGridAutofitNumvlines: 10,
	    backgroundGridAutofitNumhlines: 10,
//	    backgroundGridVlines: false,
	    backgroundGridBorder: false,
	    colors: [ 'aqua' ],
	    key: ['Filter Pressure PSI' ],
	    keyPosition: 'gutter',
	    numxticks: 10,
	    tickmarks: null,
	    labels: labels,
//	    noaxes: true,
	    textSize: 12,
	    textAngle: 45,
	    textColor: '#aaa',
	    scaleZerostart: true
	}
    }).draw();

    filterPressure_dateaxis = new RGraph.Drawing.XAxis({
	id: 'cvs3',
	y: filterPressure_line.canvas.height - 25,
	options: {
	     labels: datelabels,
	     noxaxis: true,	
        }
    }).draw()




    // Make and draw the background charts
    hall_line = new RGraph.Line({
	id: 'cvs_inside_bedrooms',
	data: data,
	options: {

	    title: "Temperatures\n",
	    titleBold: true,
	    titleSize: 12,
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: inside_ymax,
	    ymin: inside_ymin,
	    ylabelsCount: 7,
	    numyticks:7,
	    outofbounds: true,
	    backgroundGridAutofit: true,
	    backgroundGridAutofitNumvlines: 10,
	    backgroundGridAutofitNumhlines: 14,
//	    backgroundGridVlines: false,
	    backgroundGridBorder: false,
	    colors: [ 'Red','Green','Blue', 'Purple', 'Orange' ],
	    key: ['Hall Temp', 'Nikita Temp', 'Daniel Temp', 'Alex Temp', 'Guest Temp' ],
	    keyPosition: 'gutter',
	    numxticks: 10,
	    tickmarks: null,
	    labels: labels,
//	    noaxes: true,
	    textSize: 12,
	    textAngle: 45,
	    textColor: '#aaa',
	    scaleZerostart: true
	}
    }).draw();

    nikita_line = new RGraph.Line({
	id: 'cvs_inside_bedrooms',
	data: data,
	options: {
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: inside_ymax,
	    ymin: inside_ymin,
	    outofbounds: true,
	    backgroundGrid: false,
	    colors: [ 'green' ],
	    numxticks: 10,
	    tickmarks: null,
	    noaxes: true,
	    textColor: '#aaa',
	    ylabels: false,
	    scaleZerostart: true
	}
    }).draw();
  
  daniel_line = new RGraph.Line({
	id: 'cvs_inside_bedrooms',
	data: data,
	options: {
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: inside_ymax,
	    ymin: inside_ymin,
	    outofbounds: true,
	    backgroundGrid: false,
	    colors: [ 'blue' ],
	    numxticks: 10,
	    tickmarks: null,
	    noaxes: true,
	    textColor: '#aaa',
	    ylabels: false,
	    scaleZerostart: true
	}
    }).draw();

  alexander_line = new RGraph.Line({
	id: 'cvs_inside_bedrooms',
	data: data,
	options: {
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: inside_ymax,
	    ymin: inside_ymin,
	    outofbounds: true,
	    backgroundGrid: false,
	    colors: [ 'purple' ],
	    numxticks: 10,
	    tickmarks: null,
	    noaxes: true,
	    textColor: '#aaa',
	    ylabels: false,
	    scaleZerostart: true
	}
    }).draw();

  guest_line = new RGraph.Line({
	id: 'cvs_inside_bedrooms',
	data: data,
	options: {
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: inside_ymax,
	    ymin: inside_ymin,
	    outofbounds: true,
	    backgroundGrid: false,
	    colors: [ 'orange' ],
	    numxticks: 10,
	    tickmarks: null,
	    noaxes: true,
	    textColor: '#aaa',
	    ylabels: false,
	    scaleZerostart: true
	}
    }).draw();

    // Make and draw the background charts
    kitchendining_line = new RGraph.Line({
	id: 'cvs_inside_downstairs',
	data: data,
	options: {

	    title: "Downstairs Temperatures\n",
	    titleBold: true,
	    titleSize: 12,
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: inside_ymax,
	    ymin: inside_ymin,
	    ylabelsCount: 7,
	    numyticks:7,
	    outofbounds: true,
	    backgroundGridAutofit: true,
	    backgroundGridAutofitNumvlines: 10,
	    backgroundGridAutofitNumhlines: 14,
//	    backgroundGridVlines: false,
	    backgroundGridBorder: false,
	    colors: [ 'Red','Green' ],
	    key: [ 'Kitchen/Dining Temp', 'GreatRoom/Office Temp' ],
	    keyPosition: 'gutter',
	    numxticks: 10,
	    tickmarks: null,
	    labels: labels,
//	    noaxes: true,
	    textSize: 12,
	    textAngle: 45,
	    textColor: '#aaa',
	    scaleZerostart: true
	}
    }).draw();

  greatroom_line = new RGraph.Line({
	id: 'cvs_inside_downstairs',
	data: data,
	options: {
	    gutterRight: gutterRight,
	    gutterLeft: gutterLeft,
	    gutterTop: gutterTop,
	    gutterBottom: gutterBottom,
	    ymax: inside_ymax,
	    ymin: inside_ymin,
	    outofbounds: true,
	    backgroundGrid: false,
	    colors: [ 'green' ],
	    numxticks: 10,
	    tickmarks: null,
	    noaxes: true,
	    textColor: '#aaa',
	    ylabels: false,
	    scaleZerostart: true
	}
    }).draw();


    tempdateaxis_inside = new RGraph.Drawing.XAxis({
	id: 'cvs_inside_bedrooms',
	y: pooltemp_line.canvas.height - 25,
	options: {
	     labels: datelabels,
	     noxaxis: true,	
	     hmargin: 10,
	}
    }).draw()

    tempdateaxis_inside_downstairs = new RGraph.Drawing.XAxis({
	id: 'cvs_inside_downstairs',
	y: pooltemp_line.canvas.height - 25,
	options: {
	     labels: datelabels,
	     noxaxis: true,
	     hmargin: 10,
	}
    }).draw()


    updateDate()
    updateAutomation()
    getOutSideTempData()
    getInSideTempData()
}
function updateAutomation() {
	automation("GET_SETTINGS")
	setTimeout(updateAutomation,60000)
}
Date.prototype.timeNow = function () {
	     return ((this.getHours() < 10)?"0":"") + this.getHours() +":"+ ((this.getMinutes() < 10)?"0":"") + this.getMinutes() +":"+ ((this.getSeconds() < 10)?"0":"") + this.getSeconds();
}


function updateDate() {
	var t=new Date()
	document.getElementById("clock").innerHTML="<small>"+t.timeNow()+"</small>"
 	document.getElementById("Clock_time").innerHTML=t.timeNow()

	setTimeout(updateDate,1000)
}

// drawOutside() - Draws in the new information on graph
function drawOutside(temperatures) {
	// Reset the canvas
	RGraph.clear(humidity_line.canvas);
	RGraph.clear(patiotemp_line.canvas);
	RGraph.clear(pumptemp_line.canvas);
	RGraph.clear(pooltemp_line.canvas);
	RGraph.clear(filterPressure_line.canvas);

	// lasttemp is the index of the last entry that will have data
	var lasttemp=temperatures.length-2
	
	document.getElementById("patiotemp").innerHTML="<small>Patio Temp</small><br/>"+temperatures[lasttemp].d.patiotemp
	document.getElementById("pumptemp").innerHTML="<small>Pump Temp</small><br/>"+temperatures[lasttemp].d.pumptemp
	document.getElementById("pooltemp").innerHTML="<small>Water Temp</small><br/>"+temperatures[lasttemp].d.pooltemp
	document.getElementById("patiotemp_m").innerHTML="<small>Patio Temp</small><br/>"+temperatures[lasttemp].d.patiotemp
	document.getElementById("pumptemp_m").innerHTML="<small>Pump Temp</small><br/>"+temperatures[lasttemp].d.pumptemp
	document.getElementById("pooltemp_m").innerHTML="<small>Water Temp</small><br/>"+temperatures[lasttemp].d.pooltemp
	spa_temp=temperatures[lasttemp].d.pooltemp
        document.getElementById("SpaHeater_Temp").innerHTML="<span style='color:red;font-size: 500%;font-weight: bold;'>"+spa_temp+"</span>"

	/**
	* Create the Label Array
	*/
	for(var i=0;i<=lasttemp;i++) {
		var dt=temperatures[i].timestamp.split(" ")
		var t=dt[1].split(":")
		if (t[1]=='00' || t[1]=='30') {
			labels[i]=t[0]+":"+t[1]
		} else {
			labels[i]=''
		}
		if (t[0] == '12' && t[1]=='00') {
			datelabels[i]=dt[0]
		} else if (t[0] == '00' && t[1]=='00') {
			datelabels[i]='|'
		} else {
			datelabels[i]=''
		}
		
		humidity_line.original_data[0][i]=temperatures[i].d.humidity
		patiotemp_line.original_data[0][i]=temperatures[i].d.patiotemp
		pumptemp_line.original_data[0][i]=temperatures[i].d.pumptemp
		pooltemp_line.original_data[0][i]=temperatures[i].d.pooltemp
		filterPressure_line.original_data[0][i]=temperatures[i].d.filterpressure
	}
	
	document.getElementById("updateTime").innerHTML=temperatures[lasttemp].timestamp.split(" ")[1]
	document.getElementById("updateTime_m").innerHTML=temperatures[lasttemp].timestamp.split(" ")[1]
	
	humidity_line.draw();
	patiotemp_line.draw();
	pumptemp_line.draw();
	pooltemp_line.draw();
	filterPressure_line.draw();
	tempdateaxis.draw();
	humiditydateaxis.draw();
	filterPressure_dateaxis.draw();
	
}

// drawInside() - Draws in the new information on graph
function drawInside(temperatures) {
	// Reset the canvas
	RGraph.clear(hall_line.canvas);
	RGraph.clear(nikita_line.canvas);
	RGraph.clear(daniel_line.canvas);
	RGraph.clear(alexander_line.canvas);
	RGraph.clear(guest_line.canvas);
	RGraph.clear(kitchendining_line.canvas);
	RGraph.clear(greatroom_line.canvas);

	// lasttemp is the index of the last entry that will have data
	var lasttemp=temperatures.length-2

	/**
	* Create the Label Array
	*/
	for(var i=0;i<=lasttemp;i++) {
		var dt=temperatures[i].timestamp.split(" ")
		var t=dt[1].split(":")
		if (t[1]=='00' || t[1]=='30') {
			labels[i]=t[0]+":"+t[1]
		} else {
			labels[i]=''
		}
		if (t[0] == '12' && t[1]=='00') {
			datelabels[i]=dt[0]
		} else if (t[0] == '00' && t[1]=='00') {
			datelabels[i]='|'
		} else {
			datelabels[i]=''
		}
		
		hall_line.original_data[0][i]=temperatures[i].d.UpstairsHall
		nikita_line.original_data[0][i]=temperatures[i].d.NikitaBedroom
		daniel_line.original_data[0][i]=temperatures[i].d.DanielBedroom
		alexander_line.original_data[0][i]=temperatures[i].d.AlexanderBedroom
		guest_line.original_data[0][i]=temperatures[i].d.GuestBedroom
		kitchendining_line.original_data[0][i]=temperatures[i].d.KitchenDining
		greatroom_line.original_data[0][i]=temperatures[i].d.GreatRoomOffice
	}
	
	document.getElementById("updateTimeInside").innerHTML=temperatures[lasttemp].timestamp.split(" ")[1]
	
	hall_line.draw();
	nikita_line.draw();
	daniel_line.draw();
	alexander_line.draw();
	guest_line.draw();
	kitchendining_line.draw();
	greatroom_line.draw();
	tempdateaxis_inside.draw();
	tempdateaxis_inside_downstairs.draw();
}
function sprinkerTimerSet() {
    SprinklerTimer++;
    document.getElementById("sprinklerTimer").innerHTML=SprinklerTimer
    SprinklerTimerObj=setTimeout(sprinkerTimerSet,1000)
}
function updateSprinklerTimer() {
	var SprinklerSecs=parseInt(document.getElementById("sprinklerTurnOffSelect").value)
	var t=new Date()
	var newSecs=t.getSeconds()+SprinklerSecs

	t.setSeconds(newSecs);
	document.getElementById("sprinklerTurnOffTime").innerHTML="Sprinklers Off at: "+t.timeNow()
	clearTimeout(SprinklerTimerObj)
	SprinklerTimerObj=setTimeout(function() {automation('SPRINKLERS_OFF')},SprinklerSecs*1000)
}

function sprinklerCtrl(zone) {
    if (SprinklerState == "OFF" || SprinklerZone != zone) {

        if (SprinklerState=="OFF") {
            //Turn the sprinklers on which will advance the current zone
            automation('SPRINKLERS_ON')
            SprinklerTimer=0
            clearTimeout(SprinklerTimerObj)
            setTimeout(function() {sprinklerCtrl(zone)},15000)
            SprinklerTimerObj=setTimeout(sprinkerTimerSet,1000)
        } else {
            // Turn the sprinklers off
            automation('SPRINKLERS_OFF')
            SprinklerTimer=0
            clearTimeout(SprinklerTimerObj)
            setTimeout(function() {sprinklerCtrl(zone)},15000)
            SprinklerTimerObj=setTimeout(sprinkerTimerSet,1000)
        }
    } else {
        document.getElementById("sprinklerTimer").innerHTML=""
	clearTimeout(SprinklerTimerObj)
        if (SprinklerState != "OFF") document.getElementById("sprinklerTurnOff").style.visibility="visible"
    }
}

function sendVmailNote(mbox,msgnum) {
    var notedata=document.getElementById('msgNote'+msgnum).value
    var action='UPDATE_VMAIL&msgnum='+msgnum+'&mbox='+mbox+'&Note='+encodeURI(notedata)
    automation(action)
}

function automation(action) {
    var xhttp=new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (xhttp.readyState == 4 && xhttp.status == 200) {
            var t=new Date()
            var xmldata=xhttp.responseXML
            // The XML will have 3 main sections:
            // <X10 settings> which contain the values of all the X10 modules
            // <settings> which contain the pool settings
            // <vmail> -- one section per voicemail
            // The <setting> tag will be used in both X10settings and in the settings section

            var settings=xmldata.getElementsByTagName("setting")
            for (var i=0;i<settings.length;i++) {
                var id=settings[i].getAttribute("name")+"_"+settings[i].childNodes[0].nodeValue
                // Do something with the "id" if desired
                
                if (settings[i].getAttribute("name")=="MainPump") {
                    id=settings[i].getAttribute("name")+"_RPM"
                    document.getElementById(id).innerHTML="<small>RPM:</small>"+settings[i].childNodes[0].nodeValue
                }
                if (settings[i].getAttribute("name")=="SpaHeater") {
                    spa_heater_on_off=settings[i].childNodes[0].nodeValue
                    if (spa_heater_on_off=="on") {
                        document.getElementById('SpaHeater_Target').innerHTML=spa_temp_target.toString()
                    } else {
                        document.getElementById('SpaHeater_Target').innerHTML=spa_heater_on_off
                    }
                    document.getElementById("SpaHeater_OnOff").innerHTML="SPA&nbsp;HEATER:"+spa_heater_on_off
                    document.getElementById("SpaHeater_Temp").innerHTML="<span style='color:red;font-size: 500%;font-weight: bold;'>"+spa_temp+"</span>"

                }
                if (settings[i].getAttribute("name")=="SpaTempTarget") {
                    spa_temp_target=parseInt(settings[i].childNodes[0].nodeValue)
                    \$('#SPATEMP_SLIDER').slider('setValue',spa_temp_target);	
                }

                if (settings[i].getAttribute("name")=="garage_door") {
                    id=settings[i].getAttribute("name")
                    if (settings[i].childNodes[0].nodeValue=="off") {
                        document.getElementById(id).innerHTML="OPEN"
                        document.getElementById(id).style.color="red"
                        
                        if (t.getHours() >= 21 || t.getHours() <= 6) {
                                document.getElementById('GarageDoorOpen_time').innerHTML=t.toString()
                                \$("#clockpopup").modal("hide")
                                \$("#voicemailpopup").modal("hide")
                                \$("#GarageDoorOpen").modal()
                                if ((t.getMinutes() % 5)==0 && disableGarageDoorSpeech==0 ) {
                                         var msg = new SpeechSynthesisUtterance('Check The Garage Door');
                                         window.speechSynthesis.speak(msg);
                                } else if (disableGarageDoorSpeech==1) {
                                        document.getElementById('disableGarageDoorSpeechButton').innerHTML="Speech Disabled"
                                        document.getElementById(id).style.backgroundColor="red"
                                }
                        }
                    } else {
                        document.getElementById(id).innerHTML="closed"
                        document.getElementById(id).style.color="green"
                    }
                }
            }
            var SpaTimer=xmldata.getElementsByTagName("SpaTimer")

            if (SpaTimer.length==1) {
                document.getElementById("SpaReadyTime").value=SpaTimer[0].getAttribute("on")
                document.getElementById("SpaStopTime").value=SpaTimer[0].getAttribute("off")
            } else {
                document.getElementById("SpaReadyTime").value=""
                document.getElementById("SpaStopTime").value=""
            }

            var sprinklers=xmldata.getElementsByTagName("sprinklers")

            SprinklerZone=sprinklers[0].getAttribute('zone')
            SprinklerState=sprinklers[0].getAttribute('state')
            if (SprinklerState == "OFF" ) {
                document.getElementById("sprinklerStateText").innerHTML="Sprinklers Off"
		document.getElementById("sprinklerTurnOff").style.visibility="hidden"
                var imagesrc="/sprinklers/sprinkler_off.png"
            } else if (SprinklerState == "ON" ) {
                document.getElementById("sprinklerStateText").innerHTML="Zone "+SprinklerZone+" On"
                var imagesrc="/sprinklers/sprinkler_zone"+sprinklers[0].getAttribute('zone')+".png"
            }

            var zone_image=document.getElementById('sprinklerState');
            zone_image.src=imagesrc

            document.getElementById("exteriorOnTime").innerHTML="Lights on at "+xmldata.getElementsByTagName("lightson")[0].getAttribute('time')+" PM"


            var vmail=xmldata.getElementsByTagName("vmail")
	    \$('#vmail_table').empty();
            \$('#vmail_table').append(vmailhead)
	
            for(i=0;i<vmail.length;i++) {
                var mbox=vmail[i].getElementsByTagName("mbox")[0].childNodes[0].nodeValue
                var msgnum=vmail[i].getElementsByTagName("msgnum")[0].childNodes[0].nodeValue
                var timestamp=vmail[i].getElementsByTagName("timestamp")[0].childNodes[0].nodeValue
                var callerID=vmail[i].getElementsByTagName("callerID")[0].childNodes[0].nodeValue
                var duration=vmail[i].getElementsByTagName("duration")[0].childNodes[0].nodeValue
                var note=vmail[i].getElementsByTagName("note")[0].childNodes;
		if (note.length > 0) {
                     var notedata=vmail[i].getElementsByTagName("note")[0].childNodes[0].nodeValue
                } else {
                     var notedata=""
                }
                
                var vmailhtml='<tr style="font-size: 250%" id="msg'+msgnum+'">'+
                              '<td rowspan=2>'+ msgnum +
                        '<br><button id="delete'+msgnum+'" onclick="automation('+"'"+'DELETE_VMAIL&msgnum='+msgnum+'&mbox='+mbox+"'"+')"      type="button" class="btn btn-lg" >DELETE</button>'+
                              '</td>'+
                              '<td class="text-center">'+timestamp.split(" ")[0]+'<br>'+timestamp.split(" ")[1]+'</td>'
                if (vmail[i].getAttribute("new") == "YES") {
                              vmailhtml=vmailhtml+'<td style="font-weight:bold;color:red">'+callerID
                } else {
                              vmailhtml=vmailhtml+'<td style="font-weight:bold">'+callerID
                }
                              var noteID='msgNote'+msgnum
                              if (document.getElementById(noteID)) notedata=document.getElementById(noteID).value

                              vmailhtml=vmailhtml+'<br><textarea id="'+noteID+'" style="font-size: 50%;font-weight:normal">'+notedata+'</textarea>'
                              vmailhtml=vmailhtml+'<button style="font-size: 50%;" id="updateNote'+msgnum+'" onclick="sendVmailNote('+"'"+mbox+"','"+msgnum+"'"+')">UPDATE</button></td>'
                              vmailhtml=vmailhtml+'<td>'+duration+'</td>'+

                              '</tr>'+
                        '<tr valign=center><td colspan=3>'+
                        '<audio controls preload="none" style="width:100%"><source src="http://pizza.goldfarbs.net/voicemail/default/2201/'+mbox+'/msg'+msgnum+'.wav" type="audio/wav"></audio></td>'+

                        '</tr>';

                \$('#vmail_table').append(vmailhtml)

                if (vmail[i].getAttribute("new") == "YES") {
                        // Close any other modals that are open
                        document.getElementById('NewVoicemail_time').innerHTML=t.toString()

                        \$("#GarageDoorOpen").modal("hide")
                        \$("#clockpopup").modal("hide")
                        \$("#voicemailpopup").modal()
                }
            }
        }
    };

    var URL="http://pizza.goldfarbs.net/cgi-bin/automation.cgi?ACTION="+action
    xhttp.open("GET", URL, true);
    xhttp.send();

}
</script>
</head>
<body onLoad="createCharts()">

<div class="container">
  <div class="scroller scroller-left"><i class="glyphicon glyphicon-chevron-left" style="font-size:300%;"></i></div>
  <div class="scroller scroller-right"><i class="glyphicon glyphicon-chevron-right" style="font-size:300%;"></i></div>
  <div class="wrapper">
  <ul class="nav nav-pills list">
    <li ><h1 style="font-size: 250%;" id="clock"></h1></li>
    <li ><h1 >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</h1></li>
    <li style="font-size: 300%;" class="active"><a data-toggle="pill" href="#home">&nbsp;Temps&nbsp;</a></li>
    <li style="font-size: 300%;"><a data-toggle="pill" href="#InsideTemps">Inside</a></li>
    <li style="font-size: 300%;"><a data-toggle="pill" href="#PoolMenu">Pool</a></li>
    <li style="font-size: 300%;"><a data-toggle="pill" href="#HouseMenu">House</a></li>
    <li style="font-size: 300%;"><a data-toggle="pill" href="#SpaMenu">Spa</a></li>
    <li style="font-size: 300%;"><a data-toggle="pill" href="#VmailMenu">Vmail</a></li>
    <li style="font-size: 300%;"><a data-toggle="pill" href="#CalMenu">Calendar</a></li>

  </ul>
  </div>
  <div class="tab-content">
    <div id="home" class="tab-pane fade in active">
      <hr style="height:12px;border:0;box-shadow: inset 0 12px 12px -12px rgba(0, 0, 0, 0.5);"/>
      <div class="row">
        <div class="col-sm-4">
          <center><h1 id="patiotemp" style="color:red;font-size: 500%;font-weight: bold;"><small>Patio Temp</small><br/>0</h1></center>
        </div>
        <div class="col-sm-4">
          <center><h1 id="pumptemp" style="color:green;font-size: 500%;font-weight: bold;"><small>Pump Temp</small><br/>0</h1></center>
        </div>
        <div class="col-sm-4">
          <center><h1 id="pooltemp" style="color:blue;font-size: 500%;font-weight: bold;"><small>Water Temp</small><br/>0</h1></center>
        </div>
        <span id="updateTime">00:00:00</span>
      </div>
      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>
      <div class="row">
        <div class="col-md-12">
          <canvas id="cvs" width="800" height="400">[No canvas support]</canvas>
        </div>
      </div>
      <div class="row">
        <div class="col-md-12">
          <canvas id="cvs2" width="800" height="400">[No canvas support]</canvas>
        </div>
      </div>
      <div class="row">
        <div class="col-sm-2">
          <a href="http://pizza.goldfarbs.net/cgi-bin/house1.cgi?DataSize=180"   class="btn btn-info btn-lg" role="button" style="width:100px">3 Hours</a>
        </div>
        <div class="col-sm-2">
          <a href="http://pizza.goldfarbs.net/cgi-bin/house1.cgi?DataSize=360"   class="btn btn-info btn-lg" role="button" style="width:100px">6 Hours</a>
        </div>
        <div class="col-sm-2">
          <a href="http://pizza.goldfarbs.net/cgi-bin/house1.cgi?DataSize=720"  class="btn btn-info btn-lg" role="button" style="width:100px">12 Hours</a>
        </div>
        <div class="col-sm-2">
          <a href="http://pizza.goldfarbs.net/cgi-bin/house1.cgi?DataSize=1440"  class="btn btn-info btn-lg" role="button" style="width:100px">24 Hours</a>
        </div>
        <div class="col-sm-2">
          <a href="http://pizza.goldfarbs.net/cgi-bin/house1.cgi?DataSize=2880"  class="btn btn-info btn-lg" role="button" style="width:100px">2 Days</a>
        </div>
        <div class="col-sm-2">
          <a href="http://pizza.goldfarbs.net/cgi-bin/house1.cgi?DataSize=10080" class="btn btn-info btn-lg" role="button" style="width:100px">1 Week</a>
        </div>
      </div>
    </div>
    <div id="InsideTemps" class="tab-pane fade in active">
      <hr style="height:12px;border:0;box-shadow: inset 0 12px 12px -12px rgba(0, 0, 0, 0.5);"/>
      <div class="row">
        <div class="col-md-2">
           <span id="updateTimeInside">00:00:00</span>
        </div>
      </div>
      <div class="row">
        <div class="col-md-12">
          <canvas id="cvs_inside_bedrooms" width="800" height="400">[No canvas support]</canvas>
        </div>
      </div>
      <div class="row">
        <div class="col-md-12">
          <canvas id="cvs_inside_downstairs" width="800" height="400">[No canvas support]</canvas>
        </div>
      </div>
    </div>
    <div id="PoolMenu" class="tab-pane fade">
      <hr style="height:12px;border:0;box-shadow: inset 0 12px 12px -12px rgba(0, 0, 0, 0.5);"/>
      <div class="row">
        <div class="row">
          <div class="col-sm-2"><span style="font-size: 200%">Pump:</span></div>
          <div class="col-sm-2"><button id="MainPump_on"  onClick="automation('MAIN_PUMP_ON')"  type="button" class="btn btn-info btn-lg ">ON</button></div>
          <div class="col-sm-2"><button id="MainPump_off" onClick="automation('MAIN_PUMP_OFF')" type="button" class="btn btn-info btn-lg ">OFF</button></div>
          <div class="col-sm-2">&nbsp;</div>
          <div class="col-sm-2" ><h3 id="MainPump_RPM"><center><small>RPM:</small><br/>3450</center></h3></div>
        </div>
      </div>
      <div class="row">
        <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>
        <div class="col-sm-6">
          <h2>Features:</h2>
          <div class="row">
            <div class="col-sm-4"><span style="font-size: 150%">Waterfalls:</span></div>
            <div class="col-sm-4"><button id="Waterfall_on"  onclick="automation('TURN_ON_WATERFALL')"  type="button" class="btn btn-info btn-lg">ON</button></div>
            <div class="col-sm-4"><button id="Waterfall_off" onclick="automation('TURN_OFF_WATERFALL')" type="button" class="btn btn-info btn-lg">OFF</button></div>
          </div>
          <div class="row">
            <div class="col-sm-4"><span style="font-size: 150%">Bubblers:</span></div>
            <div class="col-sm-4"><button id="Bubblers_on"  onclick="automation('TURN_ON_BUBBLER')"  type="button" class="btn btn-info btn-lg">ON</button></div>
            <div class="col-sm-4"><button id="Bubblers_off" onclick="automation('TURN_OFF_BUBBLER')" type="button" class="btn btn-info btn-lg">OFF</button></div>
          </div>
          <div class="row">
            <div class="col-sm-4"><span style="font-size: 150%">Sprays:</span></div>
            <div class="col-sm-4"><button id="Sprays_on"    onclick="automation('TURN_ON_SPRAY')"    type="button" class="btn btn-info btn-lg">ON</button></div>
            <div class="col-sm-4"><button id="Sprays_off"   onclick="automation('TURN_OFF_SPRAY')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
          </div>
          <div class="row">
            <div class="col-sm-4"><span style="font-size: 150%">Returns:</span></div>
            <div class="col-sm-4"><button id="Return_on"    onclick="automation('TURN_ON_RETURN')"    type="button" class="btn btn-info btn-lg">ON</button></div>
            <div class="col-sm-4"><button id="Return_off"   onclick="automation('TURN_OFF_RETURN')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
          </div>
        </div>
        <div class="col-sm-6">
          <div class="col-md-12">
            <canvas id="cvs3" width="400" height="400">[No canvas support]</canvas>
          </div>
        </div>
      </div>
      <div class="row">
        <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>
        <h2>Pool Light:</h2>
        <div class="row">
          <div class="col-md-2 col-sm-4"><button id="PoolLight_off"     onclick="automation('POOL_COLOR&Color=off')"     type="button" class="btn btn-lg"         style="width:130px;">OFF</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_Magenta" onclick="automation('POOL_COLOR&Color=Magenta')" type="button" class="btn btn-lg" style="width:130px;color:white;background-color:magenta;">Magenta</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_Green"   onclick="automation('POOL_COLOR&Color=Green')"   type="button" class="btn btn-lg" style="width:130px;color:white;background-color:rgb(0,255,0);"  >Green</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_Blue"    onclick="automation('POOL_COLOR&Color=Blue')"    type="button" class="btn btn-lg" style="width:130px;color:white;background-color:blue;"   >Blue</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_Red"     onclick="automation('POOL_COLOR&Color=Red')"     type="button" class="btn btn-lg" style="width:130px;color:white;background-color:red;"    >Red</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_White"   onclick="automation('POOL_COLOR&Color=White')"   type="button" class="btn btn-lg" style="width:130px;color:black;background-color:white;"  >White</button></div>
        </div>
        <div class="row">
          <div class="col-md-2 col-sm-4"><button id="PoolLight_SAM"        onclick="automation('POOL_COLOR&Color=SAM')"        type="button" class="btn btn-lg" style="width:130px;color:white;background: url(http://pizza.goldfarbs.net/images/SAM.png)        repeat-x;">SAM</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_Party"      onclick="automation('POOL_COLOR&Color=Party')"      type="button" class="btn btn-lg" style="width:130px;color:white;background: url(http://pizza.goldfarbs.net/images/Party.png)      repeat-x;">Party</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_Caribbean"  onclick="automation('POOL_COLOR&Color=Caribbean')"  type="button" class="btn btn-lg" style="width:130px;color:black;background: url(http://pizza.goldfarbs.net/images/Caribbean.png)  repeat-x;">Caribbean</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_American"   onclick="automation('POOL_COLOR&Color=American')"   type="button" class="btn btn-lg" style="width:130px;color:black;background: url(http://pizza.goldfarbs.net/images/American.png)   repeat-x;">American</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_Cal_Sunset" onclick="automation('POOL_COLOR&Color=Cal_Sunset')" type="button" class="btn btn-lg" style="width:130px;color:black;background: url(http://pizza.goldfarbs.net/images/Cal_Sunset.png) repeat-x;">Cal_Sunset</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_Royal"      onclick="automation('POOL_COLOR&Color=Royal')"      type="button" class="btn btn-lg" style="width:130px;color:white;background: url(http://pizza.goldfarbs.net/images/Royal.png)      repeat-x;">Royal</button></div>
        </div>
        <div class="row">
          <div class="col-md-2 col-sm-4"><button id="PoolLight_Romance" onclick="automation('POOL_COLOR&Color=Romance')" type="button" class="btn btn-lg" style="width:130px;color:white;background: url(http://pizza.goldfarbs.net/images/Romance.png) repeat-x;">Romance</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_HOLD"    onclick="automation('POOL_COLOR&Color=HOLD')"    type="button" class="btn btn-lg" style="width:130px;">HOLD</button></div>
          <div class="col-md-2 col-sm-4"><button id="PoolLight_RECALL"  onclick="automation('POOL_COLOR&Color=RECALL')"  type="button" class="btn btn-lg" style="width:130px;">RECALL</button></div>
        </div>
        <div class="row">
        </div>
      </div>
    </div>
    <div id="HouseMenu" class="tab-pane fade">
      <hr style="height:12px;border:0;box-shadow: inset 0 12px 12px -12px rgba(0, 0, 0, 0.5);"/>
      <div class="row">
        <div class="col-sm-2">
          <button id="ALL_LIGHTS_ON" onclick="automation('ALL_LIGHTS_ON')"  type="button" class="btn btn-danger btn-lg" style="width:130px;">All Lights On</button>
        </div>
        <div class="col-sm-2">&nbsp;</div>
        <div class="col-sm-2">&nbsp;</div>
        <div class="col-sm-2">
          <button id="ALL_LIGHTS_OFF" onclick="automation('ALL_LIGHTS_OFF')"  type="button" class="btn btn-danger btn-lg"  style="width:130px;">All Lights Off</button>
        </div>
      </div>
      <h3>Exterior Lights</h3>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Front:</span><br><span id="exteriorOnTime">&nbsp;</span></div>
        <div class="col-sm-2"><button id="EXTERIOR_FRONT_ON"  onclick="automation('EXTERIOR_FRONT_ON')"  type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="EXTERIOR_FRONT_OFF" onclick="automation('EXTERIOR_FRONT_OFF')" type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Rear:</span><br>&nbsp;</div>
        <div class="col-sm-2"><button id="EXTERIOR_REAR_ON"    onclick="automation('EXTERIOR_REAR_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="EXTERIOR_REAR_OFF"   onclick="automation('EXTERIOR_REAR_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Northeast:</span><br>&nbsp;</div>
        <div class="col-sm-2"><button id="EXTERIOR_NE_ON"    onclick="automation('EXTERIOR_NE_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="EXTERIOR_NE_OFF"   onclick="automation('EXTERIOR_NE_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Courtyard:</span><br>&nbsp;</div>
        <div class="col-sm-2"><button id="COURTYARD_ON"    onclick="automation('COURTYARD_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="COURTYARD_OFF"   onclick="automation('COURTYARD_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>

      <div class="row">
        <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>


        <div class="col-sm-6">
          <div class="row">
            <div class="col-sm-4"><span style="font-size: 150%">Sprinklers:</span></div>
            <div class="col-sm-4"><button id="SPRINKLERS_ON"    onclick="automation('SPRINKLERS_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
            <div class="col-sm-4"><button id="SPRINKLERS_OFF"   onclick="automation('SPRINKLERS_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
          </div>
        </div>
        <div class="col-sm-6">
          <div class="col-md-12">
	    <table border=0><TR valign=center>
            <TD>
               <img id="sprinklerState" src="http://pizza.goldfarbs.net/sprinklers/sprinkler_small.png" usemap="#sprinklerMap">
            </TD>

            <TD align=center>
               <H2 id="sprinklerStateText">Sprinklers Off</H2><br>
               <span id="sprinklerTurnOff" style="visibility:hidden;" ><select class="form-control" id="sprinklerTurnOffSelect" onChange="updateSprinklerTimer()">
<option>TURN SPRINKLERS OFF:</option>
<option value=300>5 Minutes</option>
<option value=600>10 Minutes</option>
<option value=1200>20 Minutes</option>
<option value=1800>30 Minutes</option>
<option value=3600>60 Minutes</option>
</select><br><span id="sprinklerTurnOffTime"></span></span><br>
               <span id="sprinklerTimer"> </span>
            </TD>
            </table>
<map id="sprinklerMap" name="sprinklerMap">
   <area shape="poly" alt="" title="" coords="52,124,126,115,128,85,135,86,138,66,126,63,125,51,102,49" onclick="sprinklerCtrl(1)" href='#' />
   <area shape="poly" alt="" title="" coords="98,160,138,122,139,90,142,74,187,130,145,154,134,154" onclick="sprinklerCtrl(2)" href='#' />
   <area shape="poly" alt="" title="" coords="82,37,101,10,126,39,127,49,94,44,94,44" onclick="sprinklerCtrl(3)" href='#' />
   <area shape="poly" alt="" title="" coords="90,127,84,151,6,157,5,136,15,113,38,126,38,126" onclick="sprinklerCtrl(4)" href='#' />
   <area shape="poly" alt="" title="" coords="21,108,57,17,38,117" onclick="sprinklerCtrl(5)" target="" href='#' />
<!-- Created by Online Image Map Editor (http://wwwmaschek.hu/imagemap/index) -->
</map>

          </div>
        </div>
      </div>
      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>
      <div class="row">
        <div class="row">
          <div class="col-sm-4"><span style="font-size: 150%">Garage Door:</span></div>
          <div class="col-sm-4"><span style="font-size: 150%" id="garage_door">unknown</span></div>
        </div>
      </div>
      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Pond Pump:</span></div>
        <div class="col-sm-2"><button id="PONDPUMP_ON"    onclick="automation('PONDPUMP_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="PONDPUMP_OFF"   onclick="automation('PONDPUMP_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>
      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Pond Lights:</span></div>
        <div class="col-sm-2"><button id="PONDLIGHTS_ON"    onclick="automation('PONDLIGHTS_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="PONDLIGHTS_OFF"   onclick="automation('PONDLIGHTS_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>
      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>
      <h3>Interior Lights</h3>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">David Lamp:</span></div>
        <div class="col-sm-2"><button id="DAVIDLAMP_ON"    onclick="automation('DAVIDLAMP_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="DAVIDLAMP_OFF"   onclick="automation('DAVIDLAMP_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
        <div class="col-sm-2"><button id="DAVIDLAMP_25PCT"   onclick="automation('DAVIDLAMP_DIM&dimlevel=17')"   type="button" class="btn btn-info btn-lg">25</button></div>
        <div class="col-sm-2"><button id="DAVIDLAMP_50PCT"   onclick="automation('DAVIDLAMP_DIM&dimlevel=14')"   type="button" class="btn btn-info btn-lg">50</button></div>
        <div class="col-sm-2"><button id="DAVIDLAMP_75PCT"   onclick="automation('DAVIDLAMP_DIM&dimlevel=12')"   type="button" class="btn btn-info btn-lg">75</button></div>

<!--        <div class="col-sm-6">Dim&nbsp;&nbsp;&nbsp; <input id="DAVIDLAMP_SLIDER"  data-slider-id="DAVIDLAMPSLIDER" type="text" data-slider-min="0" data-slider-max="10" data-slider-step="1" data-slider-value="0"> &nbsp;&nbsp;Bright</div> -->

      </div>
<!--
      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Theatre Lamp:</span></div>
        <div class="col-sm-2"><button id="THEATRELAMP_ON"    onclick="automation('THEATRELAMP_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="THEATRELAMP_OFF"   onclick="automation('THEATRELAMP_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
        <div class="col-sm-6">Dim&nbsp;&nbsp;&nbsp; <input id="THEATRELAMP_SLIDER"  data-slider-id="THEATRELAMPSLIDER" type="text" data-slider-min="0" data-slider-max="10" data-slider-step="1" data-slider-value="0"> &nbsp;&nbsp;Bright</div>
      </div>
-->
    </div>
    <div id="SpaMenu" class="tab-pane fade">
      <hr style="height:12px;border:0;box-shadow: inset 0 12px 12px -12px rgba(0, 0, 0, 0.5);"/>
      <div class="row">
        <div class="row">
          <div class="col-sm-4"><span style="font-size: 200%">Temperature&nbsp;:</span></div>
          <div class="col-sm-6">70F&nbsp;&nbsp;&nbsp; <input id="SPATEMP_SLIDER"  data-slider-id="SPATEMPSLIDER" type="text" data-slider-min="70" data-slider-max="110" data-slider-step="1" data-slider-value="70" data-slider-orientation="horizantal"/> &nbsp;&nbsp;110F</div>
          <div class="col-sm-2" ><span style="font-size: 200%">Target<br>Temp:</span>
          <span style="font-size: 200%" id="SpaHeater_Target">?</span></div>
        </div>
        <P>

        <div class="row">
          <div class="col-sm-4"><span style="font-size: 200%">Spa&nbsp;Mode:</span></div>
          <div class="col-sm-2"><button id="Spa_on"  onClick="automation('TURN_ON_SPA')"  type="button" class="btn btn-info btn-lg ">ON</button></div>
          <div class="col-sm-2"><button id="Spa_off" onClick="automation('TURN_OFF_SPA')" type="button" class="btn btn-info btn-lg ">OFF</button></div>
        </div>
        <P>
        <div class="row">
          <div class="col-sm-4"><span style="font-size: 200%">Spa&nbsp;Heater:</span></div>
          <div class="col-sm-2"><button id="Spa_heater_on"  onClick="automation('TURN_ON_SPA_HEATER')"  type="button" class="btn btn-info btn-lg ">ON</button></div>
          <div class="col-sm-2"><button id="Spa_heater_off" onClick="automation('TURN_OFF_SPA_HEATER')" type="button" class="btn btn-info btn-lg ">OFF</button></div>
        </div>
	<P>
        <div class="row">
          <div class="col-sm-4"><span style="font-size: 200%">Main&nbsp;Pump:</span></div>
          <div class="col-sm-2"><button id="MainPump_on"  onClick="automation('MAIN_PUMP_ON')"  type="button" class="btn btn-info btn-lg ">ON</button></div>
          <div class="col-sm-2"><button id="MainPump_off" onClick="automation('MAIN_PUMP_OFF')" type="button" class="btn btn-info btn-lg ">OFF</button></div>
        </div>
        <P>
        <div class="row">
          <div class="col-sm-4"><span style="font-size: 200%">Spa&nbsp;Jets:</span></div>
          <div class="col-sm-2"><button id="Spa_jets_on"  onClick="automation('TURN_ON_SPA_JETS')"  type="button" class="btn btn-info btn-lg ">ON</button></div>
          <div class="col-sm-2"><button id="Spa_jets_off" onClick="automation('TURN_OFF_SPA_JETS')" type="button" class="btn btn-info btn-lg ">OFF</button></div>
        </div>
      </div>

      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>
      <div class="row">
        <div class="col-sm-2"><span style="font-size: 200%">Spa&nbsp;Ready:</span></div>
        <div class="col-sm-2">
          <div class="input-group clockpicker" data-placement="top" data-align="left" data-donetext="Done">
            <input type="text" class="form-control" value="19:30" id="SpaReadyTime">
            <span class="input-group-addon"><span class="glyphicon glyphicon-time"></span></span>
          </div>
        </div>
        <div class="col-sm-2">&nbsp;</div>
        <div class="col-sm-2"><span style="font-size: 200%">Spa&nbsp;Off:</span></div>
        <div class="col-sm-2">
          <div class="input-group clockpicker" data-placement="top" data-align="left" data-donetext="Done">
            <input type="text" class="form-control" value="21:30" id="SpaStopTime">
            <span class="input-group-addon"><span class="glyphicon glyphicon-time"></span></span>
          </div>
        </div>
      </div>
      <P>
      <div class="row">
          <div class="col-sm-4">&nbsp;</div>
          <div class="col-sm-2"><button id="CancelSpaSched"  onClick="automation('SPASCHEDULE')"  type="button" class="btn btn-info btn-lg ">CANCEL&nbsp;SPA&nbsp;SCHEDULE</button></div>
      </div>
      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>
      <div class="row">
        <div class="col-sm-2" ><h1 id="SpaHeater_OnOff">SPA_HEATER: ?</h1></div>
      </div>
      <div class="row">
        <div class="col-sm-2" ><h1 id="SpaHeater_Temp">?</h1></div>
      </div>

    </div>
    <div id="VmailMenu" class="tab-pane fade">
      <hr style="height:12px;border:0;box-shadow: inset 0 12px 12px -12px rgba(0, 0, 0, 0.5);"/>
      <div class="row clearfix">
        <div class="col-md-12 column">
          <table class="table table-bordered table-hover" id="vmail_table">
          </table>
        </div>
      </div>
      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>
    </div>
    <div id="CalMenu" class="tab-pane fade">
      <hr style="height:12px;border:0;box-shadow: inset 0 12px 12px -12px rgba(0, 0, 0, 0.5);"/>
      <div class="row clearfix">
        <div class="col-md-12 column">
          <div id='calendar'></div>
        </div>
      </div>
      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>
    </div>
  </div>
</div>
<p></p>
<!-- Modal -->
<div class="modal fade" id="GarageDoorOpen" role="dialog">
  <div class="modal-dialog">

    <!-- Modal content-->
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">&times;</button>
        <h4 class="modal-title">GarageDoorOpen</h4>
      </div>
      <div class="modal-body">
        <h1 style='color:red'>Check the Garage Door</h1>
        <span id='GarageDoorOpen_time'>00:00:00</span>
      </div>
      <div class="modal-footer">
        <button type="button" id="disableGarageDoorSpeechButton" class="btn btn-info btn-lg" onclick="disableGarageDoorSpeech=1;this.style.backgroundColor='red';this.innerHTML='Speech Disabled'">Disable Voice Warning</button>
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>

  </div>
</div>
<div class="modal fade" id="voicemailpopup" role="dialog">
  <div class="modal-dialog">

    <!-- Modal content-->
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">&times;</button>
        <h4 class="modal-title">New Voicemail</h4>
      </div>
      <div class="modal-body">
        <h1 style='color:red'>New Voicemail&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<a data-toggle="pill" data-dismiss="modal" href="#VmailMenu" class="btn btn-primary">GOTO VMAIL</a></h1>
        <span id='NewVoicemail_time'>00:00:00</span>
      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>

  </div>
</div>
<div class="modal fade" id="clockpopup" role="dialog">
  <div class="modal-dialog">

    <!-- Modal content-->
    <div class="modal-content">
      <div class="modal-header">
        <button type="button" class="close" data-dismiss="modal">&times;</button>
        <h4 class="modal-title">Clock</h4>
      </div>
      <div class="modal-body">
        <div class="row">
          <center><h1 style='color:DimGrey;font-size:1000%;font-weight: bold;' id='Clock_time'>Clock</h1></center>
        </div>
      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>
        <div class="row">
          <div class="col-sm-4">
            <center><h1 id="patiotemp_m" style="color:red;font-size: 500%;font-weight: bold;"><small>Patio Temp</small><br/>0</h1></center>
          </div>
          <div class="col-sm-4">
            <center><h1 id="pumptemp_m" style="color:green;font-size: 500%;font-weight: bold;"><small>Pump Temp</small><br/>0</h1></center>
          </div>
          <div class="col-sm-4">
            <center><h1 id="pooltemp_m" style="color:blue;font-size: 500%;font-weight: bold;"><small>Water Temp</small><br/>0</h1></center>
          </div>
          <span id="updateTime_m">00:00:00</span>
        </div>

      </div>
      <div class="modal-footer">
        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
      </div>
    </div>

  </div>
</div>

<script type="text/javascript" src="http://pizza.goldfarbs.net/bootstrap/js/horiz_tabscroll.js"></script>
<script>


//The clock will popup big with this eventListener
document.getElementById("clock").addEventListener('click',function() {
        \$("#clockpopup").modal()
},false);

\$('body').css('zoom', '110%');

\$('#calendar').fullCalendar({
    // options and callbacks
    header: {
        left: 'prev,next today',
        center: 'title',
        right: 'month,basicWeek,basicDay'
    },
    defaultDate: '$(date +%Y-%m-%d)',
    editable: true,
    eventLimit: true, // allow "more" link when too many events
    events: 'http://pizza.goldfarbs.net/cgi-bin/caldata.cgi'
});


//
//\$('#THEATRELAMP_SLIDER').slider({
//    formatter: function(value) {
//	// Only send if there is a half second pause
//	if (value == 0) return
//	var dimvalue=20-value
//        clearTimeout(DimmerTimer);
//        DimmerTimer=setTimeout(function() {automation('THEATRELAMP_DIM&dimlevel='+dimvalue.toString())},1000)
//
//        return 'Current value: ' + value;
//    }
//});
//\$('#DAVIDLAMP_SLIDER').slider({
//    formatter: function(value) {
//	// Only send if there is a half second pause
//	if (value == 0) return
//	var dimvalue=20-value
//        clearTimeout(DimmerTimer);
//        DimmerTimer=setTimeout(function() {automation('DAVIDLAMP_DIM&dimlevel='+dimvalue.toString())},1000)
//
//        return 'Current value: ' + value;
//    }
//});
\$('#SPATEMP_SLIDER').slider({
//    reversed: true,
    formatter: function(value) {
	// Only send if there is a half second pause
	if (value == 0||spa_temp_target==0||spa_temp_target==value) return
	clearTimeout(SpaTempTimer);
	SpaTempTimer=setTimeout(function() {automation('SPATEMP&temperature='+value.toString())},500);
	document.getElementById('SpaHeater_Target').innerHTML=value.toString()

        return 'Current value: ' + value;
    }
});
\$('.clockpicker').clockpicker({
    placement: 'top',
    align: 'left',
    donetext: 'Done',
//    init:             function() { console.log("colorpicker initiated");    },
//    beforeShow:       function() { console.log("before show");              },
//    afterShow:        function() { console.log("after show");               },
//    beforeHide:       function() { console.log("before hide");              },
//    afterHide:        function() { console.log("after hide");               },
//    beforeHourSelect: function() { console.log("before hour selected");     },
//    afterHourSelect:  function() { console.log("after hour selected");      },
//    beforeDone:       function() { console.log("before done");              },
    afterDone:        function() { 
	var SpaReadyTime=document.getElementById('SpaReadyTime').value
	var SpaStopTime=document.getElementById('SpaStopTime').value
	automation('SPASCHEDULE&SpaReadyTime='+SpaReadyTime+'&SpaStopTime='+SpaStopTime+'&temperature='+spa_temp_target)
	}
});
</script>
</body>
</html>
!





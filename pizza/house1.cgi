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


export DataSize=600

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
    <link rel="stylesheet" href="http://pizza.goldfarbs.net/bootstrap/css/horiz_tabscroll.css"/>
    <script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jquery/1.12.0/jquery.min.js"></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/bootstrap/js/bootstrap.min.js"></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/RGraph/libraries/RGraph.common.core.js" ></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/RGraph/libraries/RGraph.line.js" ></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/RGraph/libraries/RGraph.common.key.js" ></script>
    <script type="text/javascript" src="http://pizza.goldfarbs.net/RGraph/libraries/RGraph.drawing.xaxis.js" ></script>
    <title>Goldfarb Temperatures</title>

<script type="text/javascript">
var datasize=${DataSize}
var humidity_line, patiotemp_line, pumptemp_line, pooltemp_line,dateaxis;
var labels = new Array (datasize);
var datelabels = new Array (datasize);
var firstload=1;
var disableGarageDoorSpeech=0
var vmailhead='<tr>'+
              '<th class="text-center">#</th>'+
              '<th class="text-center">Date/Time</th>'+
              '<th class="text-center">CallerID</th>'+
              '<th class="text-center">Duration (secs)</th>'+
              '</tr>';

for(var i=0;i<datasize;i++) datelabels[i]=''

function getTempData() {
    var xhttp=new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
	if (xhttp.readyState == 4 && xhttp.status == 200) {
	    var data=JSON.parse(xhttp.responseText)

	    if (data.temperatures) {
		draw(data.temperatures)
		if (firstload==0) {
			setTimeout(getTempData,60000)
		} else {
			firstload=0
			var secstoNextMinute=(60- (new Date().getSeconds()) +5)*1000
			setTimeout(getTempData,secstoNextMinute)
		}
	    }
	}
    };
    var URL="http://pizza.goldfarbs.net/cgi-bin/tempdata1.cgi?DataSize="+datasize
    xhttp.open("GET", URL, true);
    xhttp.send();
}

function createChart() {
    var gutterLeft = 40, gutterRight = 40, gutterTop   = 100, gutterBottom = 75;

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
	    ymax: 110,
	    ymin: 40,
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
	    ymax: 110,
	    ymin: 40,
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
	    ymax: 110,
	    ymin: 40,
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

    updateDate()
    updateAutomation()
    getTempData()

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

// draw() - Draws in the new information on graph
function draw (temperatures) {
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
	
	
	// Update the counter
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
            var vmail=xmldata.getElementsByTagName("vmail")
	    \$('#vmail_table').empty();
            \$('#vmail_table').append(vmailhead)
	
            for(i=0;i<vmail.length;i++) {
                var mbox=vmail[i].getElementsByTagName("mbox")[0].childNodes[0].nodeValue
                var msgnum=vmail[i].getElementsByTagName("msgnum")[0].childNodes[0].nodeValue
                var timestamp=vmail[i].getElementsByTagName("timestamp")[0].childNodes[0].nodeValue
                var callerID=vmail[i].getElementsByTagName("callerID")[0].childNodes[0].nodeValue
                var duration=vmail[i].getElementsByTagName("duration")[0].childNodes[0].nodeValue




                
                var vmailhtml='<tr style="font-size: 250%" id="msg'+msgnum+'">'+
                              '<td rowspan=2>'+ msgnum +
                        '<br><button id="delete'+msgnum+'" onclick="automation('+"'"+'DELETE_VMAIL&msgnum='+msgnum+'&mbox='+mbox+"'"+')"      type="button" class="btn btn-lg" >DELETE</button>'+
                              '</td>'+
                              '<td class="text-center">'+timestamp.split(" ")[0]+'<br>'+timestamp.split(" ")[1]+'</td>'
                if (vmail[i].getAttribute("new") == "YES") {
                              vmailhtml=vmailhtml+'<td style="font-weight:bold;color:red">'+callerID+'</td>'
                } else {
                              vmailhtml=vmailhtml+'<td style="font-weight:bold">'+callerID+'</td>'
                }
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
<body onLoad="createChart()">

<div class="container">
  <div class="scroller scroller-left"><i class="glyphicon glyphicon-chevron-left" style="font-size:300%;"></i></div>
  <div class="scroller scroller-right"><i class="glyphicon glyphicon-chevron-right" style="font-size:300%;"></i></div>
  <div class="wrapper">
  <ul class="nav nav-pills list">
    <li ><h1 style="font-size: 250%;" id="clock"></h1></li>
    <li ><h1 >&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;</h1></li>
    <li style="font-size: 300%;" class="active"><a data-toggle="pill" href="#home">&nbsp;Temps&nbsp;</a></li>
    <li style="font-size: 300%;"><a data-toggle="pill" href="#PoolMenu">Pool</a></li>
    <li style="font-size: 300%;"><a data-toggle="pill" href="#HouseMenu">House</a></li>
    <li style="font-size: 300%;"><a data-toggle="pill" href="#SpaMenu">Spa</a></li>
    <li style="font-size: 300%;"><a data-toggle="pill" href="#VmailMenu">Vmail</a></li>

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
          <a href="http://pizza.goldfarbs.net/cgi-bin/house1.cgi?DataSize=1440"  class="btn btn-info btn-lg" role="button" style="width:100px">24 Hours</a>
        </div>
        <div class="col-sm-2">
          <a href="http://pizza.goldfarbs.net/cgi-bin/house1.cgi?DataSize=2880"  class="btn btn-info btn-lg" role="button" style="width:100px">2 Days</a>
        </div>
        <div class="col-sm-2">
          <a href="http://pizza.goldfarbs.net/cgi-bin/house1.cgi?DataSize=5760"  class="btn btn-info btn-lg" role="button" style="width:100px">4 Days</a>
        </div>
        <div class="col-sm-2">
          <a href="http://pizza.goldfarbs.net/cgi-bin/house1.cgi?DataSize=10080" class="btn btn-info btn-lg" role="button" style="width:100px">1 Week</a>
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
        <div class="col-sm-2"><span style="font-size: 150%">Front:</span></div>
        <div class="col-sm-2"><button id="EXTERIOR_FRONT_ON"  onclick="automation('EXTERIOR_FRONT_ON')"  type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="EXTERIOR_FRONT_OFF" onclick="automation('EXTERIOR_FRONT_OFF')" type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Rear:</span></div>
        <div class="col-sm-2"><button id="EXTERIOR_REAR_ON"    onclick="automation('EXTERIOR_REAR_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="EXTERIOR_REAR_OFF"   onclick="automation('EXTERIOR_REAR_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Northeast:</span></div>
        <div class="col-sm-2"><button id="EXTERIOR_NE_ON"    onclick="automation('EXTERIOR_NE_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="EXTERIOR_NE_OFF"   onclick="automation('EXTERIOR_NE_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Courtyard:</span></div>
        <div class="col-sm-2"><button id="COURTYARD_ON"    onclick="automation('COURTYARD_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="COURTYARD_OFF"   onclick="automation('COURTYARD_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>

      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Sprinklers:</span></div>
        <div class="col-sm-2"><button id="SPRINKLERS_ON"    onclick="automation('SPRINKLERS_ON')"    type="button" class="btn btn-info btn-lg">ON</button></div>
        <div class="col-sm-2"><button id="SPRINKLERS_OFF"   onclick="automation('SPRINKLERS_OFF')"   type="button" class="btn btn-info btn-lg">OFF</button></div>
      </div>

      <div class="row">
        <div class="col-sm-2"><span style="font-size: 150%">Garage Door:</span></div>
        <div class="col-sm-2"><span style="font-size: 150%" id="garage_door">unknown</span></div>
      </div>
    </div>
    <div id="SpaMenu" class="tab-pane fade">
      <hr style="height:12px;border:0;box-shadow: inset 0 12px 12px -12px rgba(0, 0, 0, 0.5);"/>
      <h3>Spa</h3>
      <hr style="border:0;height:1px;background-image: linear-gradient(to right, rgba(0, 0, 0, 0), rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0));"/>

    </div>
    <div id="VmailMenu" class="tab-pane fade">
      <hr style="height:12px;border:0;box-shadow: inset 0 12px 12px -12px rgba(0, 0, 0, 0.5);"/>

<!--        <iframe src="http://pizza.goldfarbs.net/cgi-bin/vmail.cgi?action=login&mailbox=2201&password=7765" width="100%" height="1000px" style="border:none;"></iframe> -->
      <div class="row clearfix">
        <div class="col-md-12 column">
          <table class="table table-bordered table-hover" id="vmail_table">
          </table>
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
        <h1 style='color:red'>New Voicemail</h1>
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
        \$("#clockpopup").modal({backdrop: false})
},false);

\$('body').css('zoom', '110%');
</script>
</body>
</html>
!





#!/bin/bash

cat <<!
Content-type: text/html

<html>
<head>
</head>
<body>
<script type="text/javascript">
if (!!window.EventSource) {
  var source = new EventSource('http://poolmonitor.goldfarbs.net/cgi-bin/tempdata.cgi');
}

source.onmessage = function(e) { document.body.innerHTML += e.data + '<br>'; };
source.addEventListener('message', function(e) {
  var data=JSON.parse(e.data);
 console.log(data.timestamp,data.humidity,data.patiotemp,data.pumptemp,data.pooltemp); 
}, false);

source.addEventListener('open', function(e) { }, false);

source.addEventListener('error', function(e) { if (e.readyState == EventSource.CLOSED) {  }}, false);

</script>
</body>
</html>

!


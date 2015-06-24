#!/usr/bin/python

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import subprocess

class RequestHandler(BaseHTTPRequestHandler):
    def _get_network_status(self):
        return subprocess.check_output(["ifconfig"])

    def _get_service_status(self, service):
        try:        
             stat = subprocess.check_output(["sudo", "service", service, "status"], stderr=subprocess.STDOUT)
        except:
             stat = "Not Running"

        return stat

    def _write_service_info(self, f, service):
        f.write("<b>{}</b> <br/>".format(service))
	f.write("<code>")
	for i in self._get_service_status(service):
	  f.write(i)
          if i == '\n':
            f.write("<br/>")
	f.write("</code> <br/>")
        f.write("""<a href="/{}/start">START</a> | <a href="/{}/stop">STOP</a>""".format(service, service))
        f.write("""<br/><br/>""")
   
    def _service_control(self, service, command):
        subprocess.call(["sudo", "service", service, command])

    def _writeheaders(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_HEAD(self):
        self._writeheaders()

    def do_GET(self):
        self._writeheaders()
	self.wfile.write("""<html><head><title>CRISPIN - STATUS</title>""")
	delay = 0 if self.path != "/" else 10
        self.wfile.write(""" <META http-equiv="refresh" content="{};URL=/"> """.format(delay))
	self.wfile.write("""
		<style>
			code {
		 	 width: 100em;
		 	 display: inline-block;
		  	padding: 10px;
		  	margin: 5px;
			  background: #ECECEC;
			  border-radius: 20px;
			}

			h1 {
			  font-family: serif;
			}

			a {
			  font-weight: bold;
			}
		</style>
		""")
	self.wfile.write("""</head><body>""")

        # NETWORK STATUS
        self.wfile.write("""<h1>Network Status:</h1>""")
        self.wfile.write("""<code>""")
        for l in self._get_network_status().split('\n'):
             self.wfile.write(l + """<br/>""")
        self.wfile.write("""</code>""")


        # SERVICE STATUS/CONTROL
        services = ["transmission-daemon", "openvpn"]
        self.wfile.write("""<h1>Service Status:</h1>""")
        for s in services:
            self._write_service_info(self.wfile, s)
	
	    if self.path == "/{}/start".format(s):
		self._service_control(s, "start")
	    elif self.path == "/{}/stop".format(s):
	        self._service_control(s, "stop")

        self.wfile.write("""</body></html>""")

serveraddr = ('', 8080)
srvr = HTTPServer(serveraddr, RequestHandler)
srvr.serve_forever()


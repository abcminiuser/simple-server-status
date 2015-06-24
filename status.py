#!/usr/bin/python

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import subprocess
import os
import socket


PORT     = 8080
HOSTNAME = socket.gethostname()


class ServiceStatusPage():
    services = ["transmission-daemon", "openvpn"]

    def _get_network_status(self):
        return subprocess.check_output(["ifconfig"])

    def _get_service_status(self, service):
        try:
             stat = subprocess.check_output(["sudo", "service", service, "status"], stderr=subprocess.STDOUT)
        except:
             stat = "Not Running"

        return stat

    def _write_service_info(self, output, service):
        output.write("<b>{}</b> <br/>".format(service))
        output.write("<code>")
        for i in self._get_service_status(service):
          output.write(i)
          if i == '\n':
            output.write("<br/>")
        output.write("</code> <br/>")
        output.write("""<a href="/%s/start">START</a> | <a href="/%s/stop">STOP</a>""" % (service, service))
        output.write("""<br/><br/>""")

    def _service_control(self, service, command):
        subprocess.call(["sudo", "service", service, command])

    def accept(self, path):
        return True

    def route(self, path, output):
        refresh_delay = 0 if path != "/" else 10

        output.write("""<html><head><title>%s - STATUS</title>""" % (HOSTNAME))
        output.write(""" <META http-equiv="refresh" content="%s;URL=/"> """ % (refresh_delay))
        output.write("""
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
        output.write("""</head><body>""")

        # NETWORK STATUS
        output.write("""<h1>Network Status:</h1>""")
        output.write("""<code>""")
        for l in self._get_network_status().split('\n'):
             output.write(l + """<br/>""")
        output.write("""</code>""")

        # SERVICE STATUS/CONTROL
        output.write("""<h1>Service Status:</h1>""")
        for s in self.services:
            self._write_service_info(output, s)

            if path == "/%s/start" % (s):
                self._service_control(s, "start")
            elif path == "/%s/stop" % (s):
                self._service_control(s, "stop")
        output.write("""</body></html>""")

        # LOAD AVERAGE
        load_average = os.getloadavg()
        output.write("""<h1>Load Status</h1>""")
        output.write("<code><b>5 min:</b> %.02f, <b>10 min:</b> %.02f, <b>15 min:</b> %.02f</code>" % (load_average[0], load_average[1], load_average[2]))
        output.write("""</code>""")


class RequestHandler(BaseHTTPRequestHandler):
    routers = [ ServiceStatusPage() ]

    def _find_routing(self, path):
        for router in self.routers:
            if router.accept(path):
                return router

        return None

    def _writeheaders(self, path):
        routing = self._find_routing(path)

        self.send_response(200 if routing is not None else 404)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def do_HEAD(self):
        self._writeheaders(self.path)

    def do_GET(self):
        routing = self._find_routing(self.path)

        self._writeheaders(self.path)
        routing.route(self.path, self.wfile)


serveraddr = ('', PORT)
srvr = HTTPServer(serveraddr, RequestHandler)
srvr.serve_forever()
s

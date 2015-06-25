#!/usr/bin/python

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import subprocess
import os
import socket


# Port to serve on
PORT     = 8080
# Host name to show in the page title
HOSTNAME = socket.gethostname()


class ServiceStatusPage():
    # Services whose status should be shown, and if they should be controllable
    SERVICES            = {"transmission-daemon": True, "openvpn": True}
    # Set to True to show network interface status
    SHOW_NETWORK_STATUS = True
    # Set to True to show load averages
    SHOW_LOAD_AVERAGES  = True
    # Seconds between each auto-refresh
    IDLE_REFRESH_DELAY  = 10

    def _get_network_status(self):
        try:
            stat = subprocess.check_output(["ifconfig"])
        except:
            stat = "Unable to Retrieve Network Info"

        return stat

    def _get_service_status(self, service):
        try:
             stat = subprocess.check_output(["sudo", "service", service, "status"], stderr=subprocess.STDOUT)
        except:
             stat = "Not Running"

        return stat

    def _write_service_info(self, output, service, controllable):
        output.write("<b>%s</b> <br/>" % (service))
        output.write("<code>")
        for i in self._get_service_status(service):
          output.write(i)
          if i == '\n':
            output.write("<br/>")
        output.write("</code> <br/>")
        if controllable is True:
            output.write("""<a href="/%s/start">START</a> | <a href="/%s/stop">STOP</a>""" % (service, service))
        output.write("""<br/><br/>""")

    def _service_control(self, service, command):
        subprocess.call(["sudo", "service", service, command])

    def accept(self, path):
        return True

    def route(self, path, output):
        refresh_delay = 0 if path != "/" else self.IDLE_REFRESH_DELAY

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
        if self.SHOW_NETWORK_STATUS is True:
            output.write("""<h1>Network Status:</h1>""")
            output.write("""<code>""")
            for l in self._get_network_status().split('\n'):
                 output.write(l + """<br/>""")
            output.write("""</code>""")

        # SERVICE STATUS/CONTROL
        if self.SERVICES is not None:
            output.write("""<h1>Service Status:</h1>""")
            for (s, c) in self.SERVICES.iteritems():
                self._write_service_info(output, s, c)

                if path in ["/%s/%s" % (s, c) for c in ["start", "stop"]]:
                    self._service_control(s, path.split("/")[-1])
            output.write("""</body></html>""")

        # LOAD AVERAGE
        if self.SHOW_LOAD_AVERAGES is True and hasattr(os, "getloadavg"):
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

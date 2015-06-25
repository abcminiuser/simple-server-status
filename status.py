#!/usr/bin/python

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import subprocess
import os
import socket


# Port to serve on
PORT     = 80
# Host name to show in the page title
HOSTNAME = socket.gethostname()


class Service(object):
    def __init__(self, name, title, controllable, info_url):
        self.name         = name
        self.title        = title
        self.controllable = controllable
        self.info_url     = info_url


class ServiceStatusPage():
    # Services whose status should be shown
    SERVICES            = [Service(name="transmission-daemon", title="Transmission"   , controllable=True, info_url="http://%s:9091/transmission/web/" % HOSTNAME),
                           Service(name="openvpn"            , title="Open VPN Client", controllable=True, info_url=None)]
    # Set to True to show network interface status
    SHOW_NETWORK_STATUS = True
    # Set to True to show load averages
    SHOW_LOAD_AVERAGES  = True
    # Seconds between each auto-refresh
    IDLE_REFRESH_DELAY  = 10

    def _run_and_get_output(self, command):
        try:
            return subprocess.check_output(command, stderr=subprocess.STDOUT)
        except:
            return None

    def _get_network_status(self):
        return self._run_and_get_output(["ifconfig"]) or "Unable to Retrieve Network Info"

    def _get_service_status(self, service):
        return self._run_and_get_output(["sudo", "service", service, "status"]) or "Unable to Get Status"

    def _write_service_info(self, output, service):
        output.write("""<b>%s</b> <br/>""" % (service.title))

        output.write("""<code>""")
        for i in self._get_service_status(service.name):
          output.write(i)
          if i == '\n':
            output.write("""<br/>""")
        output.write("""</code> <br/>""")
        if service.controllable is True:
            output.write("""<a href="/%s/start">START</a> | <a href="/%s/stop">STOP</a>""" % (service.name, service.name))
        if service.info_url is not None:
            output.write(""" | <a href="%s">INFO</a>""" % (service.info_url))
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
            for s in self.SERVICES:
                self._write_service_info(output, s)

                if path in ["/%s/%s" % (s.name, c) for c in ["start", "stop"]]:
                    self._service_control(s, path.split("/")[-1])
            output.write("""</body></html>""")

        # LOAD AVERAGE
        if self.SHOW_LOAD_AVERAGES is True and hasattr(os, "getloadavg"):
            load_average = os.getloadavg()
            output.write("""<h1>Load Status</h1>""")
            output.write("""<code><b>5 min:</b> %.02f, <b>10 min:</b> %.02f, <b>15 min:</b> %.02f</code>""" % (load_average[0], load_average[1], load_average[2]))
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

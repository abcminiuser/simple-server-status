#!/usr/bin/python

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import subprocess
import os
import socket


# Port to serve on
PORT     = 80
# Host name to show in the page title
HOSTNAME = socket.gethostname()


class HTML(object):
    @staticmethod
    def head(nested=None, href=None):
        return """<head>%s</head>""" % (nested)

    @staticmethod
    def title(nested=None, href=None):
        return """<title>%s</title>""" % (nested)

    @staticmethod
    def meta(nested=None, metatype=None, value=None, content=None):
       return """<META %s="%s" content="%s">""" % (metatype, value, content)

    @staticmethod
    def head(nested=None, href=None):
        return """<head>%s</head>""" % (nested)

    @staticmethod
    def a(nested=None, href=None):
        return """<a href="%s">%s</a>""" % (href, nested)

    @staticmethod
    def h1(nested=None):
        return """<h1>%s</h1>""" % (nested)

    @staticmethod
    def b(nested=None):
        return """<b>%s</b>""" % (nested)

    @staticmethod
    def code(nested=None):
        return """<code>%s</code>""" % (nested)

    @staticmethod
    def br(nested=None):
        return """<br />"""


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

    def _service_control(self, service, command):
        subprocess.call(["sudo", "service", service, command])

    def accept(self, path):
        return True

    def route(self, path, output):
        refresh_delay = 0 if path != "/" else self.IDLE_REFRESH_DELAY

        output.write("<html>")

        output.write("<head>")
        output.write(HTML.title("%s - STATUS" % (HOSTNAME)))
        output.write(HTML.meta("http-equiv", "refresh", "%s;URL=/" % (refresh_delay)))
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
        output.write("</head>")

        output.write("<body>")

        # NETWORK STATUS
        if self.SHOW_NETWORK_STATUS is True:
            output.write(HTML.h1("Network Status:"))
            output.write(HTML.code(HTML.br().join(self._get_network_status().split('\n'))))

        # SERVICE STATUS/CONTROL
        if self.SERVICES is not None:
            output.write(HTML.h1("Service Status:"))
            for service in self.SERVICES:
                output.write(HTML.b(service.title) + HTML.br())

                output.write(HTML.code("".join(i if i != '\n' else HTML.br() for i in self._get_service_status(service.name))))
                output.write(HTML.br())

                if service.controllable is True:
                    output.write(HTML.a("START", "/%s/start" % (service.name)) + " | " + HTML.a("STOP", "/%s/stop" % (service.name)))
                if service.info_url is not None:
                    output.write(" | " + HTML.a("INFO", service.info_url))

                output.write(HTML.br() * 2)

                if path in ["/%s/%s" % (service.name, c) for c in ["start", "stop"]]:
                    self._service_control(service, path.split("/")[-1])

        # LOAD AVERAGE
        if self.SHOW_LOAD_AVERAGES is True and hasattr(os, "getloadavg"):
            load_average = os.getloadavg()
            output.write(HTML.h1("Load Averages:"))
            output.write(HTML.code("%s %.02f %s %.02f %s %.02f" % (HTML.b("5 min:"), load_average[0], HTML.b("10 min:"), load_average[1], HTML.b("15 min:"), load_average[2])))

        output.write("</body>")
        output.write("</html>")

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

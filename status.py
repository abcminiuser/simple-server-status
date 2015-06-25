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
    output = None

    def __init__(self, output):
        self.output = output

    def write(self, content):
        self.output.write(content)

    def element(self, name, content, **kwargs):
        attrlist = "".join("%s=\"%s\"" % (key, value) for (key, value) in kwargs.iteritems())
        return """<%s %s>%s</%s>""" % (name, attrlist, content, name)

    def head(self, content=None, **kwargs):
        return self.element("head", content, **kwargs)

    def title(self, content=None, **kwargs):
        return self.element("title", content, **kwargs)

    def meta(self, metatype=None, value=None, content=None):
        return """<META %s="%s" content="%s">""" % (metatype, value, content)

    def a(self, content=None, **kwargs):
        return self.element("a", content, **kwargs)

    def h1(self, content=None, **kwargs):
        return self.element("h1", content, **kwargs)

    def b(self, content=None, **kwargs):
        return self.element("b", content, **kwargs)

    def code(self, content=None, **kwargs):
        return self.element("code", content, **kwargs)

    def br(self):
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

        html = HTML(output)
        html.write("<html>")

        html.write("<head>")
        html.write(html.title("%s - STATUS" % (HOSTNAME)))
        html.write(html.meta("http-equiv", "refresh", "%s;URL=/" % (refresh_delay)))
        html.write("""
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
        html.write("</head>")

        html.write("<body>")

        # NETWORK STATUS
        if self.SHOW_NETWORK_STATUS is True:
            html.write(html.h1("Network Status:"))
            html.write(html.code(html.br().join(self._get_network_status().split('\n'))))

        # SERVICE STATUS/CONTROL
        if self.SERVICES is not None:
            html.write(html.h1("Service Status:"))
            for service in self.SERVICES:
                html.write(html.b(service.title) + html.br())

                html.write(html.code("".join(i if i != '\n' else html.br() for i in self._get_service_status(service.name))))
                html.write(html.br())

                if service.controllable is True:
                    html.write(html.a("START", href="/%s/start" % (service.name)) + " | " + html.a("STOP", href="/%s/stop" % (service.name)))
                if service.info_url is not None:
                    html.write(" | " + html.a("INFO", href=service.info_url))

                html.write(html.br() * 2)

                if path in ["/%s/%s" % (service.name, c) for c in ["start", "stop"]]:
                    self._service_control(service.name, path.split("/")[-1])

        # LOAD AVERAGE
        if self.SHOW_LOAD_AVERAGES is True and hasattr(os, "getloadavg"):
            load_average = os.getloadavg()
            html.write(html.h1("Load Averages:"))
            html.write(html.code("%s %.02f %s %.02f %s %.02f" % (html.b("5 min:"), load_average[0], html.b("10 min:"), load_average[1], html.b("15 min:"), load_average[2])))

        html.write("</body>")
        html.write("</html>")


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

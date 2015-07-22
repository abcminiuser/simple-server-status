#!/usr/bin/python

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from subprocess import CalledProcessError
from datetime import timedelta
import subprocess
import os
import socket
import dbus


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

    def meta(self, metatype=None, content=None):
        return """<META %s content="%s">""" % (metatype, content)

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
    DBUS_BASE_NAME    = "org.freedesktop.DBus"
    SYSTEMD_BASE_NAME = "org.freedesktop.systemd1"
    SYSTEMD_BASE_PATH = "/org/freedesktop/systemd1"

    actions = ["start", "stop"];

    def __init__(self, name, title, controllable, info_url):
        self.name         = name
        self.title        = title
        self.controllable = controllable
        self.info_url     = info_url

        sysbus  = dbus.SystemBus()
        systemd = sysbus.get_object(self.SYSTEMD_BASE_NAME, self.SYSTEMD_BASE_PATH)
        systemd_manager = dbus.Interface(systemd, dbus_interface=("%s.Manager" % self.SYSTEMD_BASE_NAME))

        self.systemd_unit_name     = systemd_manager.LoadUnit("%s.service" % name)
        self.systemd_service       = sysbus.get_object(self.SYSTEMD_BASE_NAME, str(self.systemd_unit_name))
        self.systemd_service_props = dbus.Interface(self.systemd_service, dbus_interface=("%s.Properties" % self.DBUS_BASE_NAME))
        self.systemd_service_if    = dbus.Interface(self.systemd_service, "%s.Unit" % self.SYSTEMD_BASE_NAME)

    def __getattr__(self, name):
        return self.systemd_service_props.Get(("%s.Unit" % self.SYSTEMD_BASE_NAME), name)

    def status(self):
        return "%s / %s" % (self.LoadState, self.ActiveState)

    def action(self, operation):
        if operation in self.actions:
            getattr(self, operation)()
        else:
            raise Exception("Requested action not allowed/recognized.")

    def start(self):
        self.systemd_service_if.Start('replace')

    def stop(self):
        self.systemd_service_if.Stop('replace')


class ServiceStatusPage():
    # Base URL where the status page should be located
    BASE_URL            = "/status"

    # Services whose status should be shown
    SERVICES            = [Service(name="transmission-daemon", title="Transmission"   , controllable=True, info_url="http://%s:9091/transmission/web/" % HOSTNAME),
                           Service(name="openvpn"            , title="Open VPN Client", controllable=True, info_url=None)]
    # Set to True to show network interface status
    SHOW_NETWORK_STATUS = True
    # Set to True to show system information
    SHOW_SYSTEM_INFO    = True
    # Seconds between each auto-refresh
    IDLE_REFRESH_DELAY  = 10

    def _run_and_get_output(self, command):
        try:
            return subprocess.check_output(command, stderr=subprocess.STDOUT)
        except CalledProcessError, e:
            return e.output
        except:
            return None

    def _get_network_status(self):
        return self._run_and_get_output(["ifconfig"]) or "Unable to Retrieve Network Info"

    def _get_uptime(self):
	uptime_seconds = self._run_and_get_output(["cat", "/proc/uptime"]).split()[0]
        return str(timedelta(seconds = float(uptime_seconds))) if uptime_seconds else "Unknown"

    def accept(self, path):
        return path.startswith(self.BASE_URL)

    def route(self, path, output):
        refresh_delay = 0 if path != self.BASE_URL else self.IDLE_REFRESH_DELAY

        html = HTML(output)
        html.write("<!doctype html>")
        html.write("<html>")

        html.write("<head>")
        html.write(html.title("%s - STATUS" % (HOSTNAME)))
        html.write(html.meta("viewport", "width=device-width, initial-scale=1"))
        html.write(html.meta("http-equiv=\"refresh\"", "%s;URL=%s" % (refresh_delay, self.BASE_URL)))
        html.write("""
                <style>
                        body {
                                margin: 40px auto;
                                max-width: 1000px;
                                line-height: 1.6;
                                font-size: 18px;
                                color: #444;
                                padding: 0px 10px;
                                background: #EEEEEE;
                        }

                        code {
                                display: inline-block;
                                max-width: 1000px;
                                padding: 10px;
                                margin: 5px;
                                background: #CCCCCC;
                                border-radius: 20px;
                        }

                        h1 {
                                font-family: serif;
                        }

                        a {
                                font-family: serif;
                                font-weight: bold;
                                padding: 4px;
                                font-size: 20px;
                        }
                </style>
                """)
        html.write("</head>")

        html.write("<body>")

        # NETWORK STATUS
        if self.SHOW_NETWORK_STATUS is True:
            html.write(html.h1("Network Status:"))
            html.write(html.code(html.br().join(self._get_network_status().strip().split('\n'))))

        # SERVICE STATUS/CONTROL
        if self.SERVICES is not None:
            html.write(html.h1("Service Status:"))
            for service in self.SERVICES:
                html.write(html.b(service.title) + html.br())

                html.write(html.code(service.status()))
                html.write(html.br())

                if service.controllable is True:
                    html.write(html.a("START", href="%s/%s/start" % (self.BASE_URL, service.name)) + " | " + html.a("STOP", href="%s/%s/stop" % (self.BASE_URL, service.name)))
                if service.info_url is not None:
                    html.write(" | " + html.a("INFO", href=service.info_url))

                html.write(html.br() * 2)

                if path in ["%s/%s/%s" % (self.BASE_URL, service.name, c) for c in service.actions]:
                    service.action(path.split("/")[-1])

        # SYSTEM INFO
        if self.SHOW_SYSTEM_INFO is True:
            html.write(html.h1("System Info:"))

            load_average      = os.getloadavg()
            load_average_html = "%s %.02f %s %.02f %s %.02f" % (html.b("5 min:"), load_average[0], html.b("10 min:"), load_average[1], html.b("15 min:"), load_average[2])

            html.write(html.code("Load Averages: %s %s Uptime: %s" % (load_average_html, html.br(), self._get_uptime())))

        html.write("</body>")
        html.write("</html>")


class RequestHandler(BaseHTTPRequestHandler):
    routers       = [ ServiceStatusPage() ]
    root_redirect = routers[0].BASE_URL

    def _find_routing(self, path):
        for router in self.routers:
            if router.accept(path):
                return router

        return None

    def _writeheaders(self, path):
        routing = self._find_routing(path)

        if path == "/":
            self.send_response(301)
            self.send_header('Location', self.root_redirect)
        else:
            self.send_response(200 if routing is not None else 404)
            self.send_header('Content-type', 'text/html')

        self.end_headers()

    def do_HEAD(self):
        self._writeheaders(self.path)

    def do_GET(self):
        routing = self._find_routing(self.path)

        self._writeheaders(self.path)
        if routing is not None:
            routing.route(self.path, self.wfile)
        else:
            self.wfile.write("404 - Not found.")


serveraddr = ('', PORT)
srvr = HTTPServer(serveraddr, RequestHandler)
srvr.serve_forever()

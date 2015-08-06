# Simple Server Status

Look elsewhere.

This is just a simple quick-and-dirty Python script I made to quickly check on a local Raspberry Pi server, and remotely start and stop service daemons. It has no security built in, and probably shouldn't ever be used on anything (even the server it currently runs on).

## Dependencies

Python 2.x or 3.x should work. Requires `python-systemd` and `python-netifaces`, both of which come preinstalled on most modern Linux distros.

Assumes a system.d compatible system (originally targeted at Ubuntu MATE on a Raspberry Pi 2).

## Installation

Customize the `server-status-initd` init script to use the correct path to the server, and use the correct name. Add it to `etc/init.d` then use:

```
update-rc.d server-status-initd defaults
```

To auto-start it each boot.

## Use

By default, when it runs it spins up a webserver on port 80, with uptime, network, service and other basic info.

## License

Given how terrible it is, it would be a crime to release it into the public domain in case someone else decides to actually use it. That said, I hereby release this into the public domain anyway.

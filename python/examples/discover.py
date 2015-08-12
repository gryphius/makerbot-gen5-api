#!/usr/bin/python
import makerbotapi
import sys

if __name__ == '__main__':
    print "searching for 5th gen makerbot in your network..."
    result = makerbotapi.makerbotapi.discover()
    if len(result) == 0:
        print "no 5th gen makerbot found :("
        sys.exit(1)

    for ip, machine_name, serial in result:
        print "Found '%s' at %s , serial number=%s" % (machine_name, ip, serial)

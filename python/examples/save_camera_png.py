#!/usr/bin/python
import makerbotapi
import sys
import time
import os

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print "args: <output filename> <ip address of your gen5> <How long to record (seconds)> [<AUTH CODE>]"
        sys.exit(1)
    output_filename = sys.argv[1]
    ip_address = sys.argv[2]
    record_length = sys.argv[3]

    if len(sys.argv) > 4:
        AUTH_CODE = sys.argv[4]
    else:
        AUTH_CODE = None

    makerbot = makerbotapi.Makerbot(ip_address, auth_code=AUTH_CODE)
    if AUTH_CODE == None:
        print "Press the flashing action button on your makerbot now"
        makerbot.authenticate_fcgi()
        print "Authenticated with code", makerbot.auth_code

    makerbot.authenticate_json_rpc()

    #newpath = "\\temp\\"
    #if not os.path.exists(newpath): os.makedirs(newpath)
    record_time = int(record_length) / 2

    for x in range(0, record_time):
        # print "we're on time %d" % (x)
        out = "\\temp\\" + output_filename[:-4] + str(x).zfill(10) + ".png"
        # print out
        dir = os.getcwd() + os.path.dirname(out)
        if not os.path.exists(dir):
            # print "it doesn't exist"
            os.mkdir(dir)
        # print dir
        makerbot.save_camera_png(os.getcwd() + out)
        time.sleep(2)

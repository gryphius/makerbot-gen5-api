#!/usr/bin/python
import makerbotapi
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "args: <ip address of your gen5> [<AUTH CODE>]"
        sys.exit(1)
    ip_address = sys.argv[1]

    if len(sys.argv) > 2:
        AUTH_CODE = sys.argv[2]
    else:
        AUTH_CODE = None

    makerbot = makerbotapi.Makerbot(ip_address, auth_code=AUTH_CODE)
    if AUTH_CODE == None:
        print "Press the flashing action button on your makerbot now"
        makerbot.authenticate_fcgi()
        print "Authenticated with code ", makerbot.auth_code

    makerbot.authenticate_json_rpc()

    botstate = makerbot.get_system_information()

    # print "State:", botstate.state
    # print "Extruder Temp:", botstate.extruder_temp
    # print "Preheat:", botstate.preheat_percent, "%"

    toolhead = botstate.toolheads[0]
    print "Tool ID: ", toolhead.tool_id
    print "Filament present: ", toolhead.filament_presence
    print "Preheating: ", toolhead.preheating
    print "Index: ", toolhead.index
    print "Tool present: ", toolhead.tool_present
    print "Current temperature: ", toolhead.current_temperature
    print "Target temperature: ", toolhead.target_temperature

    #process = makerbot.get_current_process()
    process = botstate.current_process
    print "-----------CURRENT PROCESS-----------"
    if process:

        print "Process: ", process.name
        print "Cancellable: ", process.cancellable
    else:
        print "No processes running."

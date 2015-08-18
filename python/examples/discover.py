#!/usr/bin/python
import makerbotapi
import sys

if __name__ == '__main__':

    #Set up vars
    knownBotIps = []
    searching = True
    count = 0
    sleepAmount = 0.25
    
    #Before we can start searching, we have to create our broadcast and answer sockets.
    sockets = makerbotapi.makerbotapi.createSockets()
    
    
    print "searching for 5th gen makerbot in your network..."
    #Start the search!
    while searching:
        #discover() takes three args: The sockets that we created earlier, and a list of known bot ip addresses.
        #   The third arg is optional, and is the amount of time discover() will sleep after it requests a response.
        #   If you don't specify a sleep amount, it defaults to 1 second.
        result = makerbotapi.makerbotapi.discover(sockets, knownBotIps, sleepAmount)
        
        #you can do other things while searching for bots.
        print "discover is non-blocking!"
        
        #If a machine is found, result will return with ('<ipaddress>','<machine name>','<serial>')
        #   Since we don't want discover() to keep finding the same bot over and over again, we add the
        #   new ip to our list of known bot ips.
        for ip, machine_name, serial in result:
            if ip not in knownBotIps:
                print "Found '%s' at %s , serial number=%s" % (machine_name, ip, serial)
                knownBotIps.append(ip)
        
        #We can print our ip list to make sure it was added correctly
        print knownBotIps
        
        #To prevent this from going on forever, we'll set searching to False after 10 iterations.
        count = count + 1
        if count > 10:
            searching = False
            
    #Lastly, we need to close up our sockets
    makerbotapi.makerbotapi.closeSockets(sockets)
#!/usr/bin/python
###########################################################################
# delta demo.
#
# (c) Dmitry Bodyonov 2005 bodyonov<>karelia.ru
###########################################################################

import delta

import socket
import string
import sys
import os
import codecs 
import locale
import getopt


############################################################
# Client wrapper
############################################################
def Call4Server (Input, Addr="127.0.0.1", Port="17777"):

    S = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        S.connect((Addr,Port))
    except socket.error:
        raise Exception, "Connection to "+str(Addr)+":"+str(Port)+" failed"

    try:
        S.send(Input)
        S.shutdown(1)
    except socket.error:
        raise Exception, "socket write error"

    try:
        Result = S.recv (4*1024)
    except socket.error:
        raise Exception, "socket read error"

    S.close()

    return Result



############################################################
# Client starts here
############################################################

# Set default values
Lang =  os.getenv("LANG")
Text=""
ReadInput = 1
Quiet = 0
PrintInput = 0
Port = 17777
Addr = "127.0.0.1"

# Parse command line arguments
try:
    (Opts, a) = getopt.getopt (sys.argv[1:], "s:p:a:l:rq")
except:
    print "Command line syntax error."
    print "Usage:  ", sys.argv[0], "[-a ADDR] [-p PORT] [-l LANG] [-r]"  
    print "         [-p PORT]   -- server's port."
    print "         [-a ADDR]   -- server's address."
    print "         [-l LANG]   -- set locale for codec (e.g. ru_RU.KOI8-R)"
    print "         [-r]        -- show user's input on the stdout"
    print "         [-q]        -- quiet"
    print "         [-s 'TEXT'] -- send string TEXT to server, and exit"
    print         
    sys.exit (1)

# Set values.
for i in Opts:
    if i[0] == "-l": Lang = i[1]
    if i[0] == "-p": Port = int(i[1])
    if i[0] == "-a": Addr = i[1]
    if i[0] == "-r": PrintInput = 1
    if i[0] == "-q": Quiet = 1
    if i[0] == "-s": 
        ReadInput = 0
        Text = i[1]


# Print banner
if not Quiet :
    print "====================================================="
    print "=          Client for the delta server.            ="
    print "====================================================="
    print " (c) Dmitry Bodyonov 2005 bodyonov<>karelia.ru       "
    print "====================================================="
    print

# We still are not sure about user's language settings,
# so we will try to create encoder.

if not Quiet :
    print " [*] Creating encoder for your locale (", Lang, ")"

try:
    locale.setlocale(locale.LC_ALL, Lang) 
    LangEnc = Lang.split(".")[1]
except:
    print "     [!] failed.  "
    LangEnc = "utf-8"
                                
    
if not Quiet :
    print " Done. Have fun! :)"
    print

Input = ""
Result = ""

while 1:
    
    try: 
        
        if ReadInput:
            
            if PrintInput:
                Input = raw_input()
                print " > ", Input
            else:
                Input = raw_input(" > ")

        else:
            if PrintInput:
                Input = Text
                print " > ", Input
            else:
                Input = Text
                
    except: 
        print "[EOF]"
        print
        break
        
    
    try:
        Input = Input.decode(LangEnc).encode("utf-8")
    except:
        print "[error]: Cannot translate your input into utf-8."
        print "         Try to use -l option in the commnad line to set correct locale."
        
    
    try:
       Result = Call4Server(Input, Addr, Port)
    except Exception, x:
        print "[error]: ", x
        continue
        
    print Result.decode("utf-8").encode(LangEnc),
   
    if Text != "" : break

    print
    


    

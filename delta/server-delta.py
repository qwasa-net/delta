#!/usr/bin/python
###########################################################################
# delta server.
#
# (c) Dmitry Bodyonov 2005 bodyonov<>karelia.ru
###########################################################################

import socket
import string
import sys
import os
import codecs 
import locale
import getopt
import select

import delta

DEBUG = 1

# Simple TCP iterative server for delta.
#######################################################
class deltaServer:

    """ 
    Implemenation of the simple TCP server for delta project.
    
    Server accepts connections from clients, reads input, and
    sends it to the delta main engine. The result of the parsing
    is sent back to the client, then connection is closed by the 
    server. 

    This server is iterative, it can serve only one client simultaneous,
    other clients must wait.

    Input string from client and result string from server are in UTF8
    encoding.
    
    """

    __SrvPort = 17777
    __SrvAddr = "127.0.0.1"
    __E = None
    __decoder = None
    __encoder = None 
    __READ_TIMEOUT = 1

        
    # Some basic initialization
    #######################################################
    def __init__ (self, dE):
        
        """ 
        Server initialization. __init__ (self, dE, codec='')
        The argument is a instance of delta to use. All dictionaries
        of the delta should be loaded before server creation.
        """
        
        # delta instance.
        self.__E = dE
        
        return

    
    # Main procedure of the server.
    #######################################################
    def Start (self, Port=17777, Addr="127.0.0.1"):
        
        """
        This procedure implements simple iterative server. It means 
        that several clients cannot be serviced simultaneously. If the 
        server is busy with the client all other clients must wait.
        
        !Note: this function is endless. It returns only on error, or 
        when SIGINT is catched.

        Function takes two optional arguments -- port number and local 
        interface address to listen on.
        """
        
        self.__SrvPort = Port
        self.__SrvAddr = Addr

        # Creating socket
        Server = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        
        # We need this for fast server restarting
        Server.setsockopt (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Binding
        Server.bind ((self.__SrvAddr, self.__SrvPort)) 
        Server.listen(5)
        
        # Main loop starts here
        while 1:
            
            # Waiting for new connections
            (Client, ClAddr) = Server.accept()

            if (DEBUG): print "Connection from", ClAddr
            
            # Trying to make client happy
            try:
                self.__Worker (Client)
            except KeyboardInterrupt: raise
            except Exception, x:
                if (DEBUG): print "Worker failed:", x

            # We dont need this anymore.
            Client.close()

        return 0

    # Worker. 
    # Client should send a line, server will send answer.
    #######################################################
    def __Worker (self, Client):
        """
        Worker is a 'private' method of the server.
        It reads input from the client, parsers it with the
        delta, and sends result back.
        """

        # Reading input
        try:
            
            # Waiting for any activity from the client
            SSet = select.select ( [Client], [], [], self.__READ_TIMEOUT)
            
            # Socket is not ready for reading
            if len(SSet[0]) == 0:
                if (DEBUG): print " [worker] read timeout"
                raise IOError, "Input reading timed out."
            
            Input = Client.recv(4*1024)

            
        except KeyboardInterrupt: raise
        except:
            raise IOError, "reading error"
        
        # Decoding
        try:
            Input = Input.replace ("\n", "")
            Input = Input.decode("utf-8")
        except KeyboardInterrupt: raise
        except:
            raise IOError, "client input decoding error"

        # Parsing
        try:
            Output = self.__E.Parse (Input)
        except KeyboardInterrupt: raise
        except:
            raise RuntimeError, "delta engine raises exception"


        if (DEBUG): 
            print " [worker] Read ("+ str(len(Input))+" bytes): " + Input
            print " [worker] Send ("+ str(len(Output))+" bytes): " + Output

        # Encoding
        try:
            Output = Output.encode("utf-8")
        except KeyboardInterrupt: raise
        except:
            raise UnicodeError, "an error occured while encoding result"

        # Sending result to the client
        try:
            Client.send (Output)
            Client.send ("\r\n")
        except KeyboardInterrupt: raise
        except:
            raise UnicodeError, "write error"
            




#####################################################################
# Starting from here
#####################################################################

# Set default values
Lang =  os.getenv("LANG")
Port = 17777
Addr = "127.0.0.1"
DEBUG = 0
# Parse command line arguments
try:
    (Opts, DictsList) = getopt.getopt (sys.argv[1:], "p:l:a:d")
except:
    print "Command line syntax error."
    print "Usage:  ", sys.argv[0], "[-p PORT]", "[-a ADDR]", "[-l LANG]", "[ dictionary file name 1 ] ..."  
    print "         [-p PORT]  -- Listen on the port number PORT."
    print "         [-a ADDR]  -- Bind to local address ADDR."
    print "         [-l LANG]  -- Set locale for engine (e.g. ru_RU.KOI8-R)."
    print "         [-d]       -- Enable debug mode."
    print         
    sys.exit (1)


if len(DictsList) == 0: DictsList = ["dictionary.xml"]

for i in Opts:
    if i[0] == "-p": Port = int(i[1])
    if i[0] == "-a": Addr = i[1]
    if i[0] == "-d": DEBUG += 1

# Creating instance of the delta.
print " [*] Creating delta instance"
E = delta.delta()

if DEBUG>1: E.SetDebugMode(DEBUG-1)

# Locale settings
try:
    locale.setlocale(locale.LC_ALL, Lang) 
except:
    print "     [!] failed to set your locale:", Lang, "problems may occure"
                                
# Loading dictionaries
for FileName in DictsList:
    print " [*] Loading dictionary (", FileName, ")"
    try:
        E.LoadDictionary (FileName)
    except:
        print "     [!] failed. "
                                      

print " [*] Creating server"
try:
    S = deltaServer(E)
except:
    print "     [!] server creation failed."


print " [*] Starting server ", Addr + ":" + str(Port)

try:

    S.Start(Port, Addr)

except KeyboardInterrupt:
    
    print "     Interrupted."

except:
    
    print "     [!] server failed."


    

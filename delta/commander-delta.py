#!/usr/bin/python
###########################################################################
# delta demo.
#
# (c) Dmitry Bodyonov 2005 bodyonov<>karelia.ru
###########################################################################

import delta
import string
import sys
import os
import re
import codecs 
import locale
import getopt

# Parse command line arguments
try:
    (Opts, DictsList) = getopt.getopt (sys.argv[1:], "pdl:")
except:
    print "Command line syntax error."
    print "Usage:  ", sys.argv[0], "[-p]", "[-l LANG]", "[ dictionary file name 1 ] ..."  
    print "         [-p]       -- print input lines also."
    print "         [-l LANG]  -- set locale for codec (e.g. ru_RU.KOI8-R)"
    print         
    sys.exit (1)

# Set default values
Lang =  os.getenv("LANG")
DEBUG=0
PrintInput = 0
if len(DictsList) == 0: DictsList = ["dictionary.xml"]

# Set values.
for i in Opts:
    if i[0] == "-l": Lang = i[1]
    if i[0] == "-p": PrintInput = 1
    if i[0] == "-d": DEBUG += 1
    

# Print banner
print "====================================================="
print "=      Command line interface for the delta.       ="
print "====================================================="
print " (c) Dmitry Bodyonov 2005 bodyonov<>karelia.ru       "
print "====================================================="
print

print " [*] Applying locale settings (" + str(Lang) + ")"

try: locale.setlocale(locale.LC_ALL, Lang) 
except:  print "     [!] failed.  "
                                
try: LangEnc = Lang.split(".")[1]
except IndexError: LangEnc = "utf-8"


# Creating instance of the delta.
print " [*] Creating delta instance"
E = delta.delta()

# Enable debugging facilities. 
E.SetDebugMode(DEBUG)

# Read dictionaries from the list.
for FileName in DictsList:
    
    print " [*] Loading dictionary (", FileName, ")"
    
    try:
        E.LoadDictionary (FileName)
    except string, e:
        print "     [!] failed with the", e
    except:
        print "     [!] failed. "
            

print " Done. Have fun! :)"
print

Input = u""

while 1:
    
    try: 
        
        if PrintInput:
            Input = raw_input()
            print " > ", Input
        else:    
            Input = raw_input("> ")
            
    except: 
        print "[EOF]"
        print
        break
        
    try:
        Input = unicode(Input, LangEnc)
    except:
        print "[error]: Cannot translate your input into python's unicode."
        print "         Try to use -l option in the commnad line."
        
    
    
    if DEBUG>3:
            Result = E.Parse (Input)
    else: 
        try:
            Result = E.Parse (Input)
        except:
            print "[error]: OOPS! Parsing error. This should not happen"
        
    print Result.encode(LangEnc)
    
    print
    

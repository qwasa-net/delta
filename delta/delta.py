#!/usr/bin/python
###########################################################################
""" 
delta, yet another answering machine. 

Simple context-free algorithm is used to generate responses 
for every input string. 

delta usage example:
    D = delta.delta()
    D.LoadDictionary ('dictionary.xml')
    print D.Parse ('hello, world!')


(c) 2005 Dmitry Bodyonov bodyonov[*]karelia.ru
"""
###########################################################################

try: import re
except: print "Unable to import module 're'"; raise SystemExit
try: import xml.sax
except: print "Unable to import module 'xml.sax'"; raise SystemExit
try: import random
except: print "Unable to import module 'random'"; raise SystemExit
try: import string
except: print "Unable to import module 'string'"; raise SystemExit

# debug level
_DEBUG = 0

# User defined exceptions class
###########################################################
class _derror:
    def __init__ (self, error=""):
        self.error = error
        


# Dictionary entry.
###########################################################
# Every entry contains list of patterns and list of answers. 
# All patterns are stored in compiled form to make searching 
# faster.
#
# This class is used by delta.__MainDictionary.
###########################################################
class _DictionaryEntry:
    """ Dictionary entry definition. """
    
    # Entry priority
    __priority = 0
    
    # Set of good patterns and precompiled RE.
    __patterns = []
    __cmp_patterns = []

    # Set of bad patterns.
    __exceptions = []
    __cmp_exceptions = []

    # List of responses.
    __responses = []


    #
    ##################################################
    def __init__ (self, Pat=[], Exc=[], Replies=[], Priority=0):
        
        self.__patterns = list(Pat)
        self.__exceptions = list(Exc)
        self.__responses = list(Replies)
        
        self.__priority = Priority
        
        self.__cmp_patterns = map (self.__RECompiler, self.__patterns)
        self.__cmp_exceptions = map (self.__RECompiler, self.__exceptions)
        

    # re.compiler wrapper (all flags at one line)
    ##################################################
    def __RECompiler (self, Pattern):
        # try to compile regular expressions
        try:
            return re.compile (Pattern, re.UNICODE) 
        except:
            if (_DEBUG>2): print "!!Error: bad regular expression = ", Pattern
            pass
                                                                

    
    ##################################################
    def Print (self):
        print self.__patterns[0]

        
    #
    ##################################################
    def Match (self, Input):
        """ 
        Method returns `match object` if input string matches at least 
        one pattern from the main set of templates, and does not match 
        any patterns from exclusion set. Otherwise None is returned.
        """

        # Match object
        MInf = None

        # Searching for good patterns
        for i in xrange (len(self.__patterns)):

            # very slow because patterns are compiled every call
            #MInf = re.search (self.__patterns[i], Input, re.UNICODE)
            
            # faster version
            MInf = self.__cmp_patterns[i].search (Input)

            if (MInf != None):
                if(_DEBUG>3): print "Matched: ", Input, "<<==>> '" + self.__patterns[i]  + "'"
                break
            else:
                if(_DEBUG>4): 
                    print "Failed: ", Input, "<<==>> '" + self.__cmp_patterns[i].pattern + "'"
                    print map(ord, Input), "<<==>> ", map(ord,self.__cmp_patterns[i].pattern)

        if (MInf == None) : return None

        # Searching for exceptions
        if len(self.__exceptions) > 0:
            
            for i in xrange (len(self.__exceptions)):
                
                if ( self.__cmp_exceptions[i].search (Input) != None ):
                    if(_DEBUG>3): print "Dropped:", self.__exceptions[i]
                    return None

        return MInf

    #
    ##################################################
    def PriorityComparator (self, other):
        """ Compare priority of two entries. """
        if self.__priority > other.__priority: return -1
        elif self.__priority < other.__priority: return 1
        return 0

    #
    ##################################################
    def GetPatterns (self):
        """ Method returns list of patterns """
        return self.__patterns

    #
    ##################################################
    def GetExceptions (self):
        """ Method returns list of exceptions. """
        return self.__exceptions

    #
    ##################################################
    def GetResponses (self):
        """ Method returns list of responses. """
        return self.__responses

    #
    ##################################################
    def SetPatterns (self, Pat=[]):
        """ Set new list of patterns """
        self.__patterns = list (Pat)
        self.__cmp_patterns = map (self.__RECompiler, self.__patterns)

    #
    ##################################################
    def SetExceptions (self, Exc=[]):
        """ Set new list of exceptions """
        self.__exceptions = list (Exc)
        self.__cmp_exceptions = map (self.__RECompiler, self.__exceptions)

    #
    ##################################################
    def SetPatterns (self, Rpl=[]):
        """ Set new list of responses """
        self.__responses = list (Rpl)



#  Dictionary definition.  
###########################################################
# Dictionary := ( (pattern)+ , (answer)+ )+
#
# Class is used by main delta class
###########################################################
class _MainDictionary:
    
    # Dictionary Entries
    __entries = []

    
    # Add new dictionary entry
    ##################################################
    def Append (self, Pat=[], Exc=[], Rpl=[], Pri=0):
        self.__entries.append (_DictionaryEntry (Pat,Exc,Rpl, Pri))
        return 

    # Remove entry from dictionary
    ##################################################
    def Remove (self, Index):
        pass
        return 

    # Sort list.
    ##################################################
    def Sort (self):
        self.__entries.sort (_DictionaryEntry.PriorityComparator)
        return 

    #
    ##################################################
    def GetEntry (self, Index):
        return self.__entries[Index]

    
    # Print dictionary contents
    ##################################################
    def Print (self):
        print len(self.__entries), " items in the dictionary"
        map (DictionaryEntry.Print, self.__entries)

    
    # Return number of entries
    ##################################################
    def Size (self):
        return len(self.__entries)
    
    # Set _DEBUG mode
    ##################################################
    def SetDebugMode (self, mode):
        global _DEBUG
        _DEBUG += mode
        return _DEBUG
    
    # Find appropriate entry.
    ##################################################
    def LookUp (self, Template):
        
        if(_DEBUG>1): print "Looking for ", Template
        
        for i in xrange (len(self.__entries)):
            MObj =  self.__entries[i].Match (Template)
            if MObj != None:
                return (self.__entries[i], MObj)
        
        return (None,None)


###########################################################
# delta -- main class of the engine.
#
###########################################################
class delta:

    """ 
    The main interface of the delta.

    Public methods of the module:
    
    LoadDictionary (FILENAME)
        Read dictionary from XML file. Method may raise an string 
        exception when file cannot be parsed for some reason. Number of
        loaded dictionary entries is returned on success.
    
    Parse(INPUT)
         Generate answer for the string INPUT based on loaded 
         dictionaries. INPUT must be an unicode string. Method
         may raise an exception. 
    
    SetDebugMode (mode) 
        Set log level, mode=0...5. When mode is >0, debug information
        will be printed on the stdout.
    
    """

    # Initialization
    def __init__ (self):

        # Create pattern for unecessary spaces used in _PreParsing
        self.__SpacesPattern = re.compile (r"[ \t\n\r]+")
        
           
    ##################################################
    def LoadDictionary (self, FileName):
        
        """ 
        Load dictionary from specified XML-file.  
        Method returns non-zero value when error occure.
        """

        try:
           
            # Handlers creation
            XHandler = _XMLLoaderHandler()
            XHandler.SetDict (self._dict)

            # Open input file
            try: IFile = open (FileName, "r")
            except:
                if (_DEBUG): print "Unable to open", FileName
                raise _derror ("Unable to read " + FileName)

            # Set input file as a input stream for the parser
            ISource = xml.sax.xmlreader.InputSource()
            ISource.setByteStream(IFile)
        
            # Parser creation
            XParser = xml.sax.make_parser()
            XParser.setContentHandler(XHandler)
        
            # XML-file parsing
            XParser.parse(ISource)
            
            IFile.close()

        except _derror, d:  raise d.error

        except:        
            if (_DEBUG): print "XML parsing error"
            raise "XML parsing error"

        # Reorder dictionary entries using priority flag.
        self._dict.Sort()

        return self._dict.Size() 
    
    
    ##################################################
    def SaveDictionary (self, FileName):
        """ 
        Save dictionary into XML-file. 
        WARNING: Not Implemented Yet.
        """
        self._dict.Print()
        print "WARNING: method delta.SaveDictionary() is not implemented yet."
        return 

    
    ##################################################
    def Print (self):
        self._dict.Print()
        return 


    ##################################################
    def SetDebugMode (self, mode):
        global _DEBUG 
        _DEBUG += mode
        if (_DEBUG>1): self._dict.SetDebugMode(mode-1)
        return _DEBUG



    ##################################################
    def Parse (self, Input):
        """
        Parse input line and generate the answer.
        """
        
        # To avoid infinite looping we will count reccurent instances.
        self.__pardepth +=1
        if (self.__pardepth > self.MAX_PARSER_DEPTH):
            if (_DEBUG) : print "That is too deep recurrence."
            self.__pardepth -= 1
            return ""

        # Make some preparations 
        Input = self._PreParsing (Input)
        
        # Searching for 'good' variant   
        (Response, MatchObject) = self._dict.LookUp(Input)
        
        if (_DEBUG): print "LookUp", Input, " === >>>", Response

        # Answer postprocessing
        Result = self._PostParsing(Input, MatchObject, Response)

        self.__pardepth -= 1
        
        return Result
    

    ##################################################
    def _PostParsing (self, Input, MatchObject, Response):
        """ 
        Post processing.
        At the first step response is selected randomly from the list
        of possible responses for the matched pattern. Then all 
        macros inside response are expanded in recurrent manner.
        """
        
        if Response == None :
            return " <<< Nothing appropriate :( >>> "
        
        # Get any response.
        SelectedResponse = random.choice(Response.GetResponses())

        if _DEBUG>1: 
            for i in Response.GetResponses():
                print " Possible answer: " , i
                
        if _DEBUG: print " Selected answer: " , SelectedResponse
            

        # Looking for marcos in the text. Every macro starts and ends 
        # with the '$' sign. (e.g. '$macro$'). Expansion rules are stored 
        # in the main dictionary. All macros are expansed in a reccurent 
        # manner, so they may have other macros inside.
        #
        # Special macros $1$, $2$ ... -- will be replaced with substrings
        # groupped in the regular expression pattern.
        # 
        # If dollar-sign '$' is needed in text it should be written 
        # as two symbols -- '$$'.
        
        
        pos = 0
        GeneratedResponse = u""
        
        while 1:

            # Searching for beginning of macro
            spos = SelectedResponse.find ("$", pos)
            
            # If '$' is not found, then just copy the rest
            # of the string to the result.
            if spos < 0:
                if (_DEBUG): print "PostProcessing: macros not found"
                GeneratedResponse += SelectedResponse[pos:]
                break

            # Searching for the end mark
            epos = SelectedResponse.find ("$", spos+1)

            # Skip endless macro name.
            if spos < 0:
                GeneratedResponse += SelectedResponse[pos:]
                break

            # Double bucks
            if epos-spos == 1:
                GeneratedResponse += SelectedResponse[pos:spos] 
                GeneratedResponse += "$"
                pos = epos + 1
                continue
                
            # Add string before macro to the final result.
            GeneratedResponse += SelectedResponse[pos:spos]
            
            # Macros with digital names are replaeced with the 
            # groupped parts of the input string.
            if string.digits.find(SelectedResponse[spos+1:epos]) > -1:
                try:
                    GeneratedResponse += MatchObject.group(int(SelectedResponse[spos+1:epos]))
                except:
                    if _DEBUG: print "Undefined group :", SelectedResponse[spos+1:epos]
                    
                pos = epos + 1
                continue
                                            
            if (_DEBUG): print "Macro expansion: ", pos, spos, epos, "'", SelectedResponse[spos:epos+1] , "'"

            # Calling main parser for the macro expansion.
            Expansion = self.Parse (SelectedResponse[spos:epos+1])

            # Result of the macro expansion is added to the final string.
            GeneratedResponse += Expansion
            
            if (_DEBUG): print "'", SelectedResponse[spos:epos+1],  "'  ==>>", Expansion

            pos = epos + 1

        return GeneratedResponse
                
    
        
    ##################################################
    def _PreParsing (self, Input):
        """ Input line pre-processing. 
        All characters are converted to lowercase and 
        unnecessary spaces are removed."""

        # Use lower case
        Input = Input.lower().strip()

        # Remove duplicated spaces
        #Input = re.sub ("[ \t\n\r]+", " ", Input)
        Input = self.__SpacesPattern.sub (" ", Input)

        return Input
    
        
    # Main dictionary 
    _dict = _MainDictionary()

    # Parser depth count
    __pardepth = 0
    MAX_PARSER_DEPTH = 25
   

# XML loader handlers
###########################################################
# This class implements XML parser handlers for LoadDictionary
# method of the delta class.
###########################################################
class _XMLLoaderHandler(xml.sax.handler.ContentHandler):
    """ Content handlers for xml loader """

    _CurrentNode = ""
    _CurrentText = ""
    _Priority = 0
    _Patterns = []
    _Exceptions = []
    _Answers = []
    
    def SetDict (self, Dict):
        self._dict = Dict

    # Beginning of the new tag.
    def startElement (self, Name, Attr):
        
        if Name == "entry":

            self._Patterns = []
            self._Answers = []
            self._Exceptions = []
            self._Priority = 0
            
            if Attr.has_key("pri"):
                self._Priority = int(Attr["pri"])
       
            if Attr.has_key("priority"):
                self._Priority = int(Attr["priority"])
                        
        if Name == "pattern" and Attr.has_key("type"):
            self._PaType = Attr["type"]
        else:
            self._PaType = ""
        
        return

    # End of the tag was found.
    def endElement (self, Name):
        
        # End of the entry, 
        if Name == "entry":
            
            self._dict.Append(self._Patterns, self._Exceptions, self._Answers,  self._Priority) 
            if (_DEBUG>2):
                try:
                    print "Entry:", len(self._Patterns), "patterns,", self._Patterns[0], \
                            " / ", len(self._Answers),  "answers,", self._Answers[0]
                except:
                    pass
            
            self._Patterns = []
            self._Answers = []
            self._Exceptions = []
            self._Priority = 0

        # Pattern for keywords.
        elif Name == "pattern":
            
            if _DEBUG>3: print "   pattern found=", self._CurrentText.strip()

            # 
            self._CurrentText = self._CurrentText.strip()
            
            if self._PaType == "":
                self._Patterns.append (self._CurrentText)
            
            elif self._PaType == "macro":
                 self._Patterns.append ( "\$" + self._CurrentText + "\$" )
            
            elif self._PaType == "exculsion" or self._PaType == "exception" or self._PaType == "exc":
                self._Exceptions.append (self._CurrentText)
        
        # Possible response for the pattern
        elif Name == "answer":
            self._Answers.append (self._CurrentText.strip())
        
        # Clean up for the next element.
        self._CurrentText = ""
        
        return

    # Save text between tags.
    def characters (self, Text):
        self._CurrentText += Text
        

# 


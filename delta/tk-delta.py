#!/usr/bin/python
###########################################################################
# delta demo.
#
# (c) Dmitry Bodyonov 2005 bodyonov<>karelia.ru
###########################################################################

import delta
import time
import sys
import getopt

import Tkinter
import tkFont

# Parse command line arguments
try:
    (Opts, DictsList) = getopt.getopt (sys.argv[1:], "p")
except:
    print "Command line syntax error."
    print "Usage:  ", sys.argv[0], "[ dictionary file name 1 ] ..."  
    print         
    sys.exit (1)

# Set default values
if len(DictsList) == 0: DictsList = ["dictionary.xml"]

class DeltaWindow:

    # 
    #################################################
    def __init__ (self, DictList=["dictionary.xml"]):
        
        self.__CreateMainWindow()
        
        self.__CreateDelta(DictList)
        
        self.__MainLoop()

    # 
    #################################################
    def __CreateMainWindow(self):
        
        self.Root = Tkinter.Tk()
        
        self.Root.title("delta")
        
        self.Root.configure(bg="darkgreen")
        self.Root.configure(cursor="top_left_arrow")
        
        #self.Root.update()

    # 
    #################################################
    def __CreateDelta (self, DictList):

        Font = tkFont.Font (family="Arial", size=10, weight="bold")
        
        LoaderLabel = Tkinter.Label(self.Root)
        LoaderLabel.configure (fg="yellow", bg="darkgreen", font=Font, width=80)
        
        LoaderLabel.grid(row=0,column=0,sticky="WES")

        self.Root.update()
        
        centerx = (self.Root.winfo_screenwidth()-self.Root.winfo_reqwidth()-100)/2
        centery = (self.Root.winfo_screenheight()-self.Root.winfo_reqheight()-100)/2
        
        self.Root.geometry (
                str(self.Root.winfo_reqwidth()) + "x" +
                str(self.Root.winfo_reqheight()) +
                "+" + str(centerx) + "+" + str(centery))
        
        self.Root.resizable(0,0)

        # Creating dElita instance
        LoaderLabel.configure(text="Creating delta instance")
        LoaderLabel.update()
        self.E = delta.delta()

        time.sleep(0.5)

        # Reading all dictionaries from the list.
        for FileName in DictsList:
            LoaderLabel.configure(text="Loading dictionary (" + FileName + ")")
            LoaderLabel.update()
            try:
                self.E.LoadDictionary (FileName)
            except:
                LoaderLabel.configure(text="Failed to load dictionary (" + FileName + ")")
                LoaderLabel.update()
        
        LoaderLabel.configure(text="Starting.....")
        LoaderLabel.update()
        time.sleep(0.5)
        
        LoaderLabel.grid_forget()

        
            

    # Hot keys handler
    #################################################
    def __EventHandler (self, e):
        if (e.keysym == "Escape"):
            self.Root.destroy()
        elif (e.keysym == "Return"):
            self.__DoInput()
                    

    # delta caller
    ################################################
    def __DoInput(self):

        Input = self.InputLine.get()
        self.InputLine.delete(0, Tkinter.END)
    
        self.MainText.configure(state=Tkinter.NORMAL)
    
        self.MainText.insert(Tkinter.END, "> " + Input + "\n","input")
    
        Result = self.E.Parse(Input)
    
        self.MainText.insert(Tkinter.END, Result + "\n\n","result")
    
        self.MainText.see (Tkinter.END)
        self.MainText.update()
        self.MainText.configure(state=Tkinter.DISABLED)

        return



    # delta caller
    ################################################
    def __MainLoop (self):

        Font = tkFont.Font (family="Arial", size=12, weight="normal")
        
        self.MainText = Tkinter.Text(self.Root)
        
        self.MainText.configure (font=Font, bg="lightyellow", fg="black", wrap="word", borderwidth=1, width=70, height=18, relief=Tkinter.FLAT)
        self.MainText.configure(state=Tkinter.DISABLED)

        self.MainText.tag_config("error", foreground="red")
        self.MainText.tag_config("input", foreground="blue")
        self.MainText.tag_config("result", foreground="red")

        self.InputLine = Tkinter.Entry(self.Root)
        self.InputLine.configure (font=Font, bg="yellow", fg="black", borderwidth=1, relief=Tkinter.FLAT)

        self.InputLine.grid(row=1, column=0, padx=3, pady=2, sticky="EW")
        self.MainText.grid(row=0, column=0,  padx=3, pady=2, sticky="WENS")

        self.Root.bind ("<Escape>", self.__EventHandler)
        self.Root.bind ("<Return>", self.__EventHandler)

        self.Root.update()
        
        centerx = (self.Root.winfo_screenwidth()-self.Root.winfo_reqwidth()-100)/2
        centery = (self.Root.winfo_screenheight()-self.Root.winfo_reqheight()-100)/2
        
        self.Root.geometry (
                str(self.Root.winfo_reqwidth()) + "x" +
                str(self.Root.winfo_reqheight()) +
                "+" + str(centerx) + "+" + str(centery))
        
        self.Root.resizable(0,0)

        self.InputLine.focus()
        
        self.Root.mainloop()




DW = DeltaWindow(DictsList)



